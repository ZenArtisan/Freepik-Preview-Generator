"""
PreviewGen - Desktop Studio
Backend Engine for pywebview + React + Framer Motion
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

import webview

from processor import (
    DEFAULT_TEXT,
    PreviewConfig,
    preview_jpeg_bytes,
    process_folder,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_3D_EXTENSIONS,
    SUPPORTED_CAD_EXTENSIONS,
)

SETTINGS_FILE = Path.home() / ".previewgen_settings.json"

# On Windows, PyInstaller --noconsole sets sys.stdout/sys.stderr to invalid handles.
# If unhandled, writing or flushing during interpreter shutdown raises OSError 22.
if sys.platform == "win32" and getattr(sys, "frozen", False):
    import ctypes
    _attached = False
    try:
        if ctypes.windll.kernel32.AttachConsole(0xFFFFFFFF):  # ATTACH_PARENT_PROCESS
            _attached = True
    except Exception:
        pass

    if _attached:
        try:
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        except Exception:
            _attached = False

    if not _attached:
        try:
            sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="replace")
        except Exception:
            sys.stdout = None
        try:
            sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="replace")
        except Exception:
            sys.stderr = None

import logging
from logging.handlers import RotatingFileHandler
import platform

def get_log_directory() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Local" / "PreviewGen" / "logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "PreviewGen"
    return Path.home() / ".local" / "state" / "previewgen"


def configure_logging() -> Path:
    log_dir = get_log_directory()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "previewgen.log"
    handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handlers: list[logging.Handler] = [handler]
    # For frozen GUI apps on Windows without console, sys.stdout can be None or raise OSError 22 on write
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        if sys.stdout is not None:
            try:
                handlers.append(logging.StreamHandler(sys.stdout))
            except Exception:
                pass
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.info(
        "Starting PreviewGen platform=%s python=%s frozen=%s",
        platform.platform(),
        sys.version,
        getattr(sys, "frozen", False),
    )
    return log_file


def show_fatal_error(title: str, message: str) -> None:
    logging.critical("%s: %s", title, message)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
            return
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            cmd = f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK" with icon stop'
            subprocess.run(["osascript", "-e", cmd], check=False)
            return
        except Exception:
            pass
    sys.stderr.write(f"\n[FATAL ERROR] {title}\n{message}\n\n")

class DesktopApi:
    def __init__(self) -> None:
        self.window: webview.Window | None = None
        self.session_zip_dir: Path | None = None
        self.cancel_event = threading.Event()
        self.batch_thread: threading.Thread | None = None

    def set_window(self, win: webview.Window) -> None:
        self.window = win

    def get_initial_state(self) -> dict[str, Any]:
        """Load persistent user preferences."""
        if SETTINGS_FILE.is_file():
            try:
                return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def save_settings(self, settings_dict: dict[str, Any]) -> bool:
        """Save user preferences to disk."""
        try:
            SETTINGS_FILE.write_text(json.dumps(settings_dict, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def browse_input_folder(self) -> str:
        """Open native OS folder selection dialog."""
        if not self.window:
            return ""
        res = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if res and len(res) > 0:
            return res[0]
        return ""

    def browse_output_folder(self) -> str:
        """Open native OS folder selection dialog."""
        if not self.window:
            return ""
        res = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if res and len(res) > 0:
            return res[0]
        return ""

    def browse_logo(self) -> str:
        """Open native OS file selection dialog for logo images."""
        if not self.window:
            return ""
        res = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Logo Images (*.png;*.webp;*.svg;*.ico;*.jpg;*.jpeg)",),
        )
        if res and len(res) > 0:
            return res[0]
        return ""

    def browse_font(self) -> str:
        """Open native OS file selection dialog for font files."""
        if not self.window:
            return ""
        res = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Font Files (*.ttf;*.otf;*.woff;*.woff2)",),
        )
        if res and len(res) > 0:
            return res[0]
        return ""

    def open_folder(self, folder_path: str) -> bool:
        """Open the target directory in Windows Explorer / macOS Finder / Linux file manager."""
        p = Path(folder_path).resolve()
        if not p.is_dir():
            return False
        try:
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
            return True
        except Exception:
            return False

    def scan_folder(self, folder_path: str) -> dict[str, Any]:
        """Scan folder for supported 2D and 3D assets, recursively traversing deep zip files."""
        p = Path(folder_path).resolve()
        if not p.is_dir():
            return {"files": [], "total": 0}

        # Clean prior session zip temp
        if self.session_zip_dir and self.session_zip_dir.exists():
            shutil.rmtree(self.session_zip_dir, ignore_errors=True)
            self.session_zip_dir = None

        direct_files = [
            f for f in p.rglob("*.*")
            if f.is_file()
            and f.suffix.lower() in SUPPORTED_EXTENSIONS
            and f.suffix.lower() != ".zip"
            and not any(part.startswith(".") and part not in (".", "..") or part == "__MACOSX" for part in f.relative_to(p).parts)
        ]
        zip_files = [
            f for f in p.rglob("*.zip")
            if f.is_file()
            and not any(part.startswith(".") and part not in (".", "..") or part == "__MACOSX" for part in f.relative_to(p).parts)
        ]

        extracted_files: list[Path] = []
        if zip_files:
            from processor import safe_extract_zip
            self.session_zip_dir = Path(tempfile.mkdtemp(prefix="previewgen_react_zip_"))
            for z in zip_files:
                sub_target = self.session_zip_dir / z.stem
                try:
                    safe_extract_zip(z, sub_target)
                    # Check for nested zips and extract them
                    nested_zips = [nz for nz in sub_target.rglob("*.zip") if nz.is_file()]
                    for nz in nested_zips:
                        try:
                            safe_extract_zip(nz, nz.parent / nz.stem)
                        except Exception:
                            pass
                except Exception as exc:
                    logging.warning("Could not safely extract archive %s: %s", z.name, exc)

            extracted_files = [
                f for f in self.session_zip_dir.rglob("*.*")
                if f.is_file()
                and f.suffix.lower() in SUPPORTED_EXTENSIONS
                and f.suffix.lower() != ".zip"
                and not any(part.startswith(".") and part not in (".", "..") or part == "__MACOSX" for part in f.relative_to(self.session_zip_dir).parts)
            ]

        all_paths = sorted(direct_files + extracted_files)
        files_payload = []
        for f in all_paths:
            ext_clean = f.suffix.upper().lstrip(".")
            files_payload.append({
                "name": f.name,
                "path": str(f.resolve()),
                "ext": ext_clean,
                "is_3d": (f.suffix.lower() in SUPPORTED_3D_EXTENSIONS and f.suffix.lower() != ".blend") or f.suffix.lower() in (".step", ".stp", ".iges", ".igs"),
            })

        return {"files": files_payload, "total": len(files_payload)}

    def render_preview(self, file_path: str, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Render live preview asynchronously and return base64 JPEG data URL."""
        source_path = Path(file_path)
        if not source_path.is_file():
            return {"error": "File does not exist"}

        # Hex to RGB tuple conversion helper
        def hex_to_rgb(h: str) -> tuple[int, int, int]:
            h = h.lstrip("#")
            if len(h) == 6:
                return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            return (255, 255, 255)

        cfg = PreviewConfig(
            text=config_dict.get("text", DEFAULT_TEXT),
            position="custom",
            opacity=float(config_dict.get("opacity", 90)) / 100.0,
            invert_triangles=bool(config_dict.get("invertTriangles", True)),
            solid_color=hex_to_rgb(config_dict.get("solidColor", "#FFFFFF")),
            text_color=hex_to_rgb(config_dict.get("textColor", "#FFFFFF")),
            has_outline=bool(config_dict.get("hasOutline", True)),
            outline_color=hex_to_rgb(config_dict.get("outlineColor", "#000000")),
            outline_thickness=int(config_dict.get("outlineThickness", 2)),
            font_scale=float(config_dict.get("fontScale", 100)) / 100.0,
            yaw=float(config_dict.get("yaw", 45)),
            pitch=float(config_dict.get("pitch", 30)),
            text_pos_x=float(config_dict.get("textPosX", 5)) / 100.0,
            text_pos_y=float(config_dict.get("textPosY", 5)) / 100.0,
            logo_path=str(config_dict.get("logoPath", "")),
            logo_scale=float(config_dict.get("logoScale", 100)) / 100.0,
            logo_opacity=float(config_dict.get("logoOpacity", 90)) / 100.0,
            logo_pos_x=float(config_dict.get("logoPosX", 88)) / 100.0,
            logo_pos_y=float(config_dict.get("logoPosY", 5)) / 100.0,
            font_path=str(config_dict.get("fontPath", "")),
        )

        try:
            jpeg_bytes, orig_w, orig_h = preview_jpeg_bytes(source_path, cfg, max_dimension=850)
            b64 = base64.b64encode(jpeg_bytes).decode("ascii")
            return {
                "dataUrl": f"data:image/jpeg;base64,{b64}",
                "width": orig_w,
                "height": orig_h,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def start_batch(self, input_folder: str, output_folder: str, config_dict: dict[str, Any]) -> None:
        """Start asynchronous batch processing on a dedicated worker thread."""
        if self.batch_thread and self.batch_thread.is_alive():
            logging.warning("Batch processing already active; ignoring duplicate request.")
            return

        self.cancel_event.clear()

        def hex_to_rgb(h: str) -> tuple[int, int, int]:
            try:
                h = h.lstrip("#")
                if len(h) == 3:
                    h = "".join(c * 2 for c in h)
                if len(h) == 6:
                    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            except Exception:
                pass
            return (255, 255, 255)

        cfg = PreviewConfig(
            text=config_dict.get("text", DEFAULT_TEXT),
            position="custom",
            opacity=float(config_dict.get("opacity", 90)) / 100.0,
            invert_triangles=bool(config_dict.get("invertTriangles", True)),
            solid_color=hex_to_rgb(config_dict.get("solidColor", "#FFFFFF")),
            text_color=hex_to_rgb(config_dict.get("textColor", "#FFFFFF")),
            has_outline=bool(config_dict.get("hasOutline", True)),
            outline_color=hex_to_rgb(config_dict.get("outlineColor", "#000000")),
            outline_thickness=int(config_dict.get("outlineThickness", 2)),
            font_scale=float(config_dict.get("fontScale", 100)) / 100.0,
            yaw=float(config_dict.get("yaw", 45)),
            pitch=float(config_dict.get("pitch", 30)),
            text_pos_x=float(config_dict.get("textPosX", 5)) / 100.0,
            text_pos_y=float(config_dict.get("textPosY", 5)) / 100.0,
            logo_path=str(config_dict.get("logoPath", "")),
            logo_scale=float(config_dict.get("logoScale", 100)) / 100.0,
            logo_opacity=float(config_dict.get("logoOpacity", 90)) / 100.0,
            logo_pos_x=float(config_dict.get("logoPosX", 88)) / 100.0,
            logo_pos_y=float(config_dict.get("logoPosY", 5)) / 100.0,
            font_path=str(config_dict.get("fontPath", "")),
        )

        def run_worker() -> None:
            def on_progress(cur: int, tot: int, msg: str) -> None:
                if self.window:
                    msg_json = json.dumps(str(msg))
                    self.window.evaluate_js(f"window.__onBatchProgress({int(cur)}, {int(tot)}, {msg_json})")

            try:
                success, failed, errors = process_folder(
                    Path(input_folder),
                    Path(output_folder),
                    cfg,
                    on_progress,
                    self.cancel_event.is_set,
                )
                if self.window:
                    err_json = json.dumps(errors[:20])
                    cancelled_str = "true" if self.cancel_event.is_set() else "false"
                    self.window.evaluate_js(f"window.__onBatchFinished({success}, {failed}, {err_json}, {cancelled_str})")
            except Exception as e:
                logging.exception("Batch execution failed")
                if self.window:
                    err_json = json.dumps([str(e)])
                    self.window.evaluate_js(f"window.__onBatchFinished(0, 1, {err_json}, false)")

        self.batch_thread = threading.Thread(target=run_worker, daemon=True)
        self.batch_thread.start()
    def cancel_batch(self) -> None:
        self.cancel_event.set()

    def cleanup(self) -> None:
        if self.session_zip_dir and self.session_zip_dir.exists():
            shutil.rmtree(self.session_zip_dir, ignore_errors=True)


def main() -> int:
    log_file = configure_logging()
    is_frozen = getattr(sys, "frozen", False)
    dev_mode = os.environ.get("PREVIEWGEN_DEV") == "1"

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MustaqeemTools.PreviewGen.App.1.0")
        except Exception:
            pass

    # Determine HTML entry path (handles frozen bundle, source dev, and production dist)
    if is_frozen:
        base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)).resolve()
    else:
        base_dir = Path(__file__).resolve().parent

    candidates = [
        base_dir / "frontend" / "dist" / "index.html",
        base_dir / "dist" / "index.html",
        base_dir / "index.html",
    ]
    if is_frozen:
        candidates.insert(0, Path(sys.executable).resolve().parent / "frontend" / "dist" / "index.html")
        candidates.insert(1, Path(sys.executable).resolve().parent / "dist" / "index.html")

    html_dist: Path | None = None
    for candidate in candidates:
        if candidate.is_file():
            html_dist = candidate
            break

    target_url: str | None = None
    if html_dist and html_dist.is_file():
        target_url = html_dist.resolve().as_uri()
        logging.info("Loaded frontend bundle from %s", html_dist)
    elif not is_frozen and dev_mode:
        import urllib.request
        try:
            urllib.request.urlopen("http://localhost:5173", timeout=0.5)
            target_url = "http://localhost:5173"
            logging.info("Development mode active: bound to Vite server http://localhost:5173")
        except Exception:
            target_url = None

    if "--smoke-test" in sys.argv or "--version" in sys.argv:
        from processor import PreviewConfig, compose_preview, SUPPORTED_EXTENSIONS
        from PIL import Image
        assert html_dist is not None and html_dist.is_file(), f"Frontend bundle missing: {candidates}"
        test_img = Image.new("RGBA", (100, 100), (99, 102, 241, 255))
        test_preview = compose_preview(test_img, PreviewConfig())
        assert test_preview.size == (100, 100)
        api = DesktopApi()
        api.cleanup()
        msg = f"[STARTUP-TEST] OK: PreviewGen initialized successfully. Bundle: {html_dist}, Formats: {len(SUPPORTED_EXTENSIONS)}"
        logging.info(msg)
        try:
            if sys.stdout is not None:
                sys.stdout.write(msg + "\n")
                sys.stdout.flush()
        except Exception:
            pass
        return 0

    if not target_url:
        err_msg = (
            "PreviewGen could not locate its required frontend bundle.\n\n"
            f"Search path: {base_dir}\n"
            "Expected file: frontend/dist/index.html\n\n"
            "Please reinstall PreviewGen or run 'npm run build' in the frontend directory."
        )
        show_fatal_error("PreviewGen - Missing Assets", err_msg)
        raise RuntimeError(err_msg)

    api = DesktopApi()
    window = webview.create_window(
        title="PreviewGen",
        url=target_url,
        js_api=api,
        width=1340,
        height=900,
        min_size=(1020, 720),
        background_color="#D6E6EF",
    )
    api.set_window(window)

    try:
        webview.start(debug=False)
    except Exception as exc:
        show_fatal_error("PreviewGen - GUI Failure", f"Failed to initialize webview window: {exc}")
        raise
    finally:
        api.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
