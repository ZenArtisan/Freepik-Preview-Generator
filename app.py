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


def ensure_desktop_shortcut() -> None:
    """Ensure an official desktop shortcut exists across Windows, macOS, and Linux."""
    try:
        if sys.platform == "win32":
            exe = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve().parent / "dist" / "PreviewGen" / "PreviewGen.exe")
            if not Path(exe).is_file():
                return
            ico = str(Path(exe).parent / "app.ico")
            if not Path(ico).is_file():
                ico = str(Path(__file__).resolve().parent / "app.ico")
            ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
if ($desktop -and (Test-Path $desktop)) {{
    $lnk = Join-Path $desktop "PreviewGen.lnk"
    if (-not (Test-Path $lnk)) {{
        $s = $wsh.CreateShortcut($lnk)
        $s.TargetPath = '{exe}'
        $s.WorkingDirectory = '{Path(exe).parent}'
        if (Test-Path '{ico}') {{ $s.IconLocation = '{ico},0' }}
        $s.Description = 'PreviewGen - Transparent PNG to JPG Preview Generator'
        $s.Save()
    }}
}}
"""
            subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script], creationflags=0x08000000)
        elif sys.platform == "darwin":
            desktop = Path.home() / "Desktop" / "PreviewGen"
            app_path = Path("/Applications/PreviewGen.app")
            if desktop.parent.exists() and not desktop.exists() and app_path.exists():
                desktop.symlink_to(app_path)
        elif sys.platform.startswith("linux"):
            desktop = Path.home() / "Desktop" / "PreviewGen.desktop"
            app_entry = Path.home() / ".local/share/applications/previewgen.desktop"
            if desktop.parent.exists() and not desktop.exists() and app_entry.exists():
                shutil.copyfile(app_entry, desktop)
                desktop.chmod(0o755)
    except Exception:
        pass


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
            f for f in p.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS and f.suffix.lower() != ".zip"
        ]
        zip_files = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() == ".zip"]

        extracted_files: list[Path] = []
        if zip_files:
            import zipfile
            self.session_zip_dir = Path(tempfile.mkdtemp(prefix="previewgen_react_zip_"))
            for z in zip_files:
                try:
                    with zipfile.ZipFile(z, "r") as zf:
                        for member in zf.infolist():
                            parts = Path(member.filename).parts
                            if any(part.startswith(".") or part == "__MACOSX" for part in parts):
                                continue
                            if member.is_dir() or member.filename.lower().endswith((".ds_store", "thumbs.db", "desktop.ini")):
                                continue
                            t = (self.session_zip_dir / f"{z.stem}_{member.filename}").resolve()
                            if not str(t).startswith(str(self.session_zip_dir.resolve())):
                                continue
                            t.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(member) as src, open(t, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                except Exception:
                    pass

            extracted_files = [
                f for f in self.session_zip_dir.rglob("*.*")
                if f.is_file()
                and f.suffix.lower() in SUPPORTED_EXTENSIONS
                and f.suffix.lower() != ".zip"
                and not any(part.startswith(".") or part == "__MACOSX" for part in f.parts)
            ]

        all_paths = sorted(direct_files + extracted_files)
        files_payload = []
        for f in all_paths:
            ext_clean = f.suffix.upper().lstrip(".")
            files_payload.append({
                "name": f.name,
                "path": str(f.resolve()),
                "ext": ext_clean,
                "is_3d": f.suffix.lower() in SUPPORTED_3D_EXTENSIONS or f.suffix.lower() in (".step", ".stp", ".iges", ".igs"),
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
            jpeg_bytes = preview_jpeg_bytes(source_path, cfg, max_dimension=850)
            b64 = base64.b64encode(jpeg_bytes).decode("ascii")
            from PIL import Image
            from io import BytesIO
            with Image.open(BytesIO(jpeg_bytes)) as img:
                w, h = img.size
            return {
                "dataUrl": f"data:image/jpeg;base64,{b64}",
                "width": w,
                "height": h,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def start_batch(self, input_folder: str, output_folder: str, config_dict: dict[str, Any]) -> None:
        """Start asynchronous batch processing on a dedicated worker thread."""
        self.cancel_event.clear()

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

        def run_worker() -> None:
            def on_progress(cur: int, tot: int, msg: str) -> None:
                if self.window:
                    clean_msg = msg.replace("'", "\\'")
                    self.window.evaluate_js(f"window.__onBatchProgress({cur}, {tot}, '{clean_msg}')")

            try:
                success, failed, errors = process_folder(
                    Path(input_folder),
                    Path(output_folder),
                    cfg,
                    on_progress,
                    self.cancel_event.is_set,
                )
                if self.window:
                    err_json = json.dumps(errors[:8])
                    cancelled = "true" if self.cancel_event.is_set() else "false"
                    self.window.evaluate_js(f"window.__onBatchFinished({success}, {failed}, {err_json}, {cancelled})")
            except Exception as e:
                if self.window:
                    self.window.evaluate_js(f"window.__onBatchFinished(0, 1, ['{str(e)}'], false)")

        self.batch_thread = threading.Thread(target=run_worker, daemon=True)
        self.batch_thread.start()

    def cancel_batch(self) -> None:
        self.cancel_event.set()

    def cleanup(self) -> None:
        if self.session_zip_dir and self.session_zip_dir.exists():
            shutil.rmtree(self.session_zip_dir, ignore_errors=True)


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MustaqeemTools.PreviewGen.App.1.0")
        except Exception:
            pass

    ensure_desktop_shortcut()

    # Determine HTML entry path (handles dev, production build, and frozen bundle)
    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", sys.executable)).resolve()
    else:
        base_dir = Path(__file__).resolve().parent

    html_dist = None
    for candidate in (
        base_dir / "frontend" / "dist" / "index.html",
        base_dir / "dist" / "index.html",
        base_dir / "index.html",
    ):
        if candidate.is_file():
            html_dist = candidate
            break
    api = DesktopApi()
    window = webview.create_window(
        title="PreviewGen",
        url=str(html_dist) if html_dist.is_file() else "http://localhost:5173",
        js_api=api,
        width=1340,
        height=900,
        min_size=(1020, 720),
        background_color="#D6E6EF",
    )
    api.set_window(window)

    try:
        webview.start(debug=False)
    finally:
        api.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
