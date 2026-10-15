from __future__ import annotations
import os
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

CHECKER_LIGHT = (245, 245, 248, 255)
CHECKER_DARK = (200, 204, 212, 255)
SOLID_COLOR = (255, 255, 255)
DEFAULT_TEXT = "100% TRANSPARENT"
SUPPORTED_3D_EXTENSIONS: tuple[str, ...] = (
    ".glb",
    ".gltf",
    ".obj",
    ".stl",
    ".ply",
    ".3mf",
    ".dae",
    ".blend",
)
SUPPORTED_CAD_EXTENSIONS: tuple[str, ...] = (
    ".dxf",
    ".dwg",
    ".max",
    ".f3d",
    ".mb",
    ".ma",
    ".step",
    ".stp",
    ".iges",
    ".igs",
)
SUPPORTED_EXTENSIONS: tuple[str, ...] = (
    ".png",
    ".webp",
    ".tif",
    ".tiff",
    ".svg",
    ".svgz",
    ".psd",
    *SUPPORTED_3D_EXTENSIONS,
    *SUPPORTED_CAD_EXTENSIONS,
    ".zip",
)


@dataclass
class PreviewConfig:
    text: str = DEFAULT_TEXT
    position: str = "top-left"            # top-left, top-right, center, bottom-left, bottom-right, custom
    opacity: float = 0.9                  # 0.0 to 1.0 (text opacity)
    invert_triangles: bool = True         # True: Left Solid, Right Transparent; False: Left Transparent, Right Solid
    solid_color: tuple[int, int, int] = (255, 255, 255)  # RGB of solid triangle
    text_color: tuple[int, int, int] = (255, 255, 255)   # RGB of text fill
    has_outline: bool = True              # Enable/disable outline stroke
    outline_color: tuple[int, int, int] = (0, 0, 0)      # RGB of outline stroke
    outline_thickness: int = 2            # 1 (thin) to 5 (extra bold)
    font_scale: float = 1.0               # 0.5 to 2.0
    # 3D View Angle & Shading
    yaw: float = 45.0                     # degrees (horizontal rotation: 0 to 360)
    pitch: float = 30.0                   # degrees (vertical elevation: -85 to 85)
    model_color: tuple[int, int, int] = (120, 130, 160)  # default studio slate
    # Freeform Text Coordinates (0.0 to 1.0 ratio of canvas width / height)
    text_pos_x: float = 0.05
    text_pos_y: float = 0.05
    # Custom Logo / Icon Branding Overlay
    logo_path: str = ""                   # Path to logo/icon file (or empty for none)
    logo_scale: float = 1.0               # Logo scale multiplier (0.2 to 3.0)
    logo_opacity: float = 0.9             # Logo opacity (0.0 to 1.0)
    logo_pos_x: float = 0.88              # Logo horizontal position (0.0 to 1.0)
    logo_pos_y: float = 0.05              # Logo vertical position (0.0 to 1.0)
    # Custom Font Support
    font_path: str = ""                   # Path to custom .ttf/.otf font file


def _font(size: int, font_path: str = "") -> ImageFont.ImageFont:
    if font_path and Path(font_path).is_file():
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except Exception:
            pass
    candidates: list[Path] = []
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR") or os.environ.get("SystemRoot") or "C:/Windows")
        fonts_dir = windir / "Fonts"
        for name in ("arialbd.ttf", "segoeuib.ttf", "calibrib.ttf", "arial.ttf"):
            candidates.append(fonts_dir / name)
    elif sys.platform == "darwin":
        for p in (
            "/System/Library/Fonts/SFProDisplay-Bold.otf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/Library/Fonts/Arial Bold.ttf",
        ):
            candidates.append(Path(p))
    else:
        for p in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ):
            candidates.append(Path(p))

    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _checker_tile(size: int) -> Image.Image:
    tile = Image.new("RGBA", (size * 2, size * 2), CHECKER_LIGHT)
    draw = ImageDraw.Draw(tile)
    draw.rectangle((size, 0, size * 2 - 1, size - 1), fill=CHECKER_DARK)
    draw.rectangle((0, size, size - 1, size * 2 - 1), fill=CHECKER_DARK)
    return tile


def make_background(
    width: int,
    height: int,
    invert_triangles: bool = True,
    solid_color: tuple[int, int, int] = SOLID_COLOR,
) -> Image.Image:
    """Create two equal-area triangles divided from bottom-left to top-right.

    invert_triangles=True:  Left is solid color, Right is checkerboard (transparent).
    invert_triangles=False: Left is checkerboard, Right is solid color.
    """
    if width < 1 or height < 1:
        raise ValueError("Invalid image dimensions")

    checker_size = max(8, min(96, round(min(width, height) / 64)))
    tile = _checker_tile(checker_size)
    checker = Image.new("RGBA", (width, height), CHECKER_LIGHT)
    for y in range(0, height, tile.height):
        for x in range(0, width, tile.width):
            checker.paste(tile, (x, y))

    solid = Image.new("RGBA", (width, height), (*solid_color, 255))

    # Triangle mask for the upper-left half
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).polygon(
        [(0, 0), (width - 1, 0), (0, height - 1)], fill=255
    )

    if invert_triangles:
        # Left half is solid color, right half is checkerboard
        background = checker.copy()
        background.paste(solid, (0, 0), mask)
    else:
        # Left half is checkerboard, right half is solid color
        background = solid.copy()
        background.paste(checker, (0, 0), mask)

    # Draw subtle separator line along diagonal with contrasting tone
    draw = ImageDraw.Draw(background)
    lum = solid_color[0] * 0.299 + solid_color[1] * 0.587 + solid_color[2] * 0.114
    sep_rgb = (225, 228, 232, 255) if lum > 120 else (80, 90, 105, 255)
    draw.line(
        [(0, height - 1), (width - 1, 0)],
        fill=sep_rgb,
        width=max(1, round(min(width, height) / 1000)),
    )
    return background


def _calculate_text_position(
    image_size: tuple[int, int],
    text_size: tuple[int, int],
    position: str = "top-left",
    object_bounds: tuple[int, int, int, int] | None = None,
) -> tuple[int, int]:
    width, height = image_size
    tw, th = text_size

    # Responsive padding proportional to resolution
    pad_x = max(24, min(140, round(width * 0.038)))
    pad_y = max(24, min(140, round(height * 0.038)))

    pos = position.lower().strip()
    if pos == "top-left":
        x = pad_x
        y = pad_y
    elif pos == "top-right":
        x = width - tw - pad_x
        y = pad_y
    elif pos == "bottom-left":
        x = pad_x
        y = height - th - pad_y
    elif pos == "bottom-right":
        x = width - tw - pad_x
        y = height - th - pad_y
    elif pos == "center":
        if object_bounds:
            left, top, right, bottom = object_bounds
            cx = (left + right) // 2
            cy = (top + bottom) // 2
        else:
            cx = width // 2
            cy = height // 2
        x = cx - tw // 2
        y = cy - th // 2
    else:
        x = pad_x
        y = pad_y

    x = max(10, min(width - tw - 10, x))
    y = max(10, min(height - th - 10, y))
    return x, y


def compose_preview(
    source: Image.Image,
    config: PreviewConfig | None = None,
    text: str | None = None,
    position: str = "top-left",
    opacity: float = 0.9,
    invert_triangles: bool = True,
) -> Image.Image:
    """Composite preview without crop, trim, resize, rotation, or distortion."""
    if config is None:
        actual_text = text if text is not None else DEFAULT_TEXT
        config = PreviewConfig(
            text=actual_text,
            position=position,
            opacity=opacity,
            invert_triangles=invert_triangles,
        )

    original = source.convert("RGBA")
    width, height = original.size
    alpha_min, alpha_max = original.getchannel("A").getextrema()
    if alpha_max == 0:
        raise ValueError("Image is completely transparent (empty canvas)")

    if alpha_min == 255:
        # Handle CAD drawings, blueprints, or renders with uniform white/black backgrounds
        import numpy as np
        arr = np.array(original)
        bg_col = arr[0, 0, :3].astype(float)
        dist = np.linalg.norm(arr[:, :, :3].astype(float) - bg_col, axis=2)
        if float(np.mean(dist < 15)) > 0.10:
            alpha = np.clip((dist / 35.0) * 255.0, 0, 255).astype(np.uint8)
            arr[:, :, 3] = alpha
            original = Image.fromarray(arr)
    bg = make_background(
        width,
        height,
        invert_triangles=config.invert_triangles,
        solid_color=config.solid_color,
    )
    result = Image.alpha_composite(bg, original)

    # ── 1. Custom Logo / Icon Branding Overlay ──
    if config.logo_path and Path(config.logo_path).is_file():
        try:
            logo_file = Path(config.logo_path)
            logo_img = load_source_image(logo_file)
            base_dim = round(min(width, height) * 0.16 * max(0.2, min(3.0, config.logo_scale)))
            lw, lh = logo_img.size
            if max(lw, lh) > 0:
                ratio = base_dim / max(lw, lh)
                target_lw = max(16, round(lw * ratio))
                target_lh = max(16, round(lh * ratio))
                logo_scaled = logo_img.resize((target_lw, target_lh), Image.Resampling.LANCZOS)

                clamped_logo_op = max(0.05, min(1.0, config.logo_opacity))
                if clamped_logo_op < 0.99:
                    lr, lg, lb, la = logo_scaled.split()
                    la = la.point(lambda p: round(p * clamped_logo_op))
                    logo_scaled.putalpha(la)

                lx = max(0, min(width - target_lw, round((width - target_lw) * max(0.0, min(1.0, config.logo_pos_x)))))
                ly = max(0, min(height - target_lh, round((height - target_lh) * max(0.0, min(1.0, config.logo_pos_y)))))

                logo_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
                logo_layer.paste(logo_scaled, (lx, ly), logo_scaled)
                result = Image.alpha_composite(result, logo_layer)
        except Exception:
            pass

    # ── 2. Watermark Text Overlay ──
    label = config.text.strip()
    if label:
        base_font_size = round(min(width, height) * 0.038 * config.font_scale)
        font_size = max(14, min(240, base_font_size))
        font = _font(font_size, config.font_path)

        draw_calc = ImageDraw.Draw(result)
        box = draw_calc.textbbox((0, 0), label, font=font, stroke_width=0)
        tw = box[2] - box[0]
        th = box[3] - box[1]

        # Use freeform position coordinates
        if config.position == "custom" or (config.text_pos_x != 0.05 or config.text_pos_y != 0.05):
            x = max(0, min(width - tw, round((width - tw) * max(0.0, min(1.0, config.text_pos_x)))))
            y = max(0, min(height - th, round((height - th) * max(0.0, min(1.0, config.text_pos_y)))))
        else:
            obj_bounds = original.getchannel("A").getbbox()
            x, y = _calculate_text_position(result.size, (tw, th), config.position, obj_bounds)

        text_layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(text_layer)

        clamped_opacity = max(0.05, min(1.0, config.opacity))
        alpha_fill = round(255 * clamped_opacity)
        fill_color = (*config.text_color, alpha_fill)

        if config.has_outline:
            multiplier = max(0.5, config.outline_thickness / 2.0)
            stroke = max(1, round(font_size * 0.075 * multiplier))
            stroke_fill = (*config.outline_color, alpha_fill)
            t_draw.text(
                (x, y),
                label,
                font=font,
                fill=fill_color,
                stroke_width=stroke,
                stroke_fill=stroke_fill,
            )
        else:
            t_draw.text(
                (x, y),
                label,
                font=font,
                fill=fill_color,
            )

        result = Image.alpha_composite(result, text_layer)
    return result.convert("RGB")

def _load_svg(source_path: Path, target_dimension: int = 3600) -> Image.Image:
    """Rasterize an SVG/SVGZ vector file to a high-resolution RGBA PIL image."""
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(str(source_path))
    if not renderer.isValid():
        raise ValueError("Invalid or unreadable SVG vector file")

    default_size = renderer.defaultSize()
    w = default_size.width()
    h = default_size.height()
    if w <= 0 or h <= 0:
        view_box = renderer.viewBoxF()
        w = max(1, round(view_box.width()))
        h = max(1, round(view_box.height()))

    if w <= 0 or h <= 0:
        w, h = 3000, 3000

    # Scale proportionally so the longest edge reaches a crisp target resolution
    max_dim = max(w, h)
    scale = min(max(target_dimension / max_dim, 1.0), 6.0)
    target_w = max(100, round(w * scale))
    target_h = max(100, round(h * scale))

    qimg = QImage(target_w, target_h, QImage.Format.Format_ARGB32_Premultiplied)
    qimg.fill(Qt.GlobalColor.transparent)

    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    qimg.save(buf, "PNG")
    buf.close()

    with Image.open(BytesIO(ba.data())) as pil_img:
        pil_img.load()
        return pil_img.convert("RGBA")


def _load_psd(source_path: Path) -> Image.Image:
    """Extract the composite layer with transparency from an Adobe Photoshop PSD file."""
    try:
        from psd_tools import PSDImage
    except ImportError:
        raise RuntimeError(
            "psd-tools is required to process PSD files. Please install it with: pip install psd-tools"
        )

    psd = PSDImage.open(source_path)
    composite = psd.composite()
    if composite is None:
        raise ValueError("Could not extract composite transparency layer from PSD")
    return composite.convert("RGBA")

def _load_dxf(source_path: Path, target_dimension: int = 2400) -> Image.Image:
    """Render an AutoCAD .dxf drawing/mesh using ezdxf and PySide6."""
    try:
        import ezdxf
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.pyqt import PyQtBackend
        from PySide6.QtWidgets import QApplication, QGraphicsScene
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtCore import Qt, QRectF, QByteArray, QBuffer, QIODevice

        app = QApplication.instance() or QApplication([])
        doc = ezdxf.readfile(str(source_path))
        msp = doc.modelspace()

        scene = QGraphicsScene()
        backend = PyQtBackend(scene)
        ctx = RenderContext(doc)
        frontend = Frontend(ctx, backend)
        frontend.draw_layout(msp)

        rect = scene.sceneRect()
        w = max(50, int(rect.width()))
        h = max(50, int(rect.height()))
        scale = min(target_dimension / max(w, h), 4.0)
        tw = max(100, int(w * scale))
        th = max(100, int(h * scale))

        qimg = QImage(tw, th, QImage.Format.Format_ARGB32_Premultiplied)
        qimg.fill(Qt.GlobalColor.transparent)
        painter = QPainter(qimg)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter, QRectF(0, 0, tw, th), rect)
        painter.end()

        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        qimg.save(buf, "PNG")
        buf.close()

        with Image.open(BytesIO(ba.data())) as pil_img:
            pil_img.load()
            return pil_img.convert("RGBA")
    except Exception as exc:
        raise RuntimeError(f"Could not render DXF file: {exc}")


def extract_dwg_thumbnail(path: Path) -> Image.Image | None:
    """Extract embedded BMP or PNG thumbnail from AutoCAD .dwg binary header."""
    import struct
    try:
        with open(path, "rb") as f:
            header = f.read(6)
            if not header.startswith(b"AC"):
                return None
            f.seek(0x0D)
            offset_val = struct.unpack("<i", f.read(4))[0]
            next_pos = 0x14 + offset_val
            f.seek(0, 2)
            if next_pos >= f.tell():
                return None
            f.seek(next_pos)
            byt_cnt_raw = f.read(1)
            if not byt_cnt_raw or byt_cnt_raw[0] <= 1:
                return None
            for _ in range(byt_cnt_raw[0]):
                code_raw = f.read(1)
                if not code_raw:
                    break
                code = code_raw[0]
                img_start, img_size = struct.unpack("<ii", f.read(8))
                if code == 2:  # BMP
                    f.seek(img_start)
                    info_header = f.read(img_size)
                    if len(info_header) >= 40:
                        bi_bits = struct.unpack("<H", info_header[14:16])[0]
                        bi_size = struct.unpack("<I", info_header[20:24])[0]
                        c_table = (4 * (2 ** bi_bits)) if bi_bits < 9 else 0
                        file_sz = 54 + c_table + bi_size
                        bmp_data = b"BM" + struct.pack("<IHHI", file_sz, 0, 0, 54 + c_table) + info_header
                        with Image.open(BytesIO(bmp_data)) as img:
                            img.load()
                            return img.convert("RGBA")
                elif code == 6:  # PNG
                    f.seek(img_start)
                    png_data = f.read(img_size)
                    with Image.open(BytesIO(png_data)) as img:
                        img.load()
                        return img.convert("RGBA")
        return None
    except Exception:
        return None


def _load_dwg(source_path: Path) -> Image.Image:
    thumb = extract_dwg_thumbnail(source_path)
    if thumb is not None:
        return thumb
    raise RuntimeError(
        "This DWG file does not contain an embedded preview thumbnail. "
        "In AutoCAD, save with THUMBSIZE enabled, or export as DXF."
    )


def extract_max_thumbnail(path: Path) -> Image.Image | None:
    """Extract embedded viewport thumbnail from Autodesk 3ds Max (.max) OLE files."""
    try:
        import olefile
        if not olefile.isOleFile(str(path)):
            return None
        with olefile.OleFileIO(str(path)) as ole:
            for sname in ole.listdir():
                s_lower = "/".join(sname).lower()
                if "thumbnail" in s_lower or "preview" in s_lower:
                    data = ole.openstream(sname).read()
                    png_idx = data.find(b"\x89PNG\r\n\x1a\n")
                    if png_idx >= 0:
                        with Image.open(BytesIO(data[png_idx:])) as img:
                            img.load()
                            return img.convert("RGBA")
                    bmp_idx = data.find(b"BM")
                    if bmp_idx >= 0:
                        with Image.open(BytesIO(data[bmp_idx:])) as img:
                            img.load()
                            return img.convert("RGBA")
            if ole.exists("\x05SummaryInformation"):
                stream = ole.openstream("\x05SummaryInformation").read()
                png_idx = stream.find(b"\x89PNG\r\n\x1a\n")
                if png_idx >= 0:
                    with Image.open(BytesIO(stream[png_idx:])) as img:
                        img.load()
                        return img.convert("RGBA")
                bmp_idx = stream.find(b"BM")
                if bmp_idx >= 0:
                    with Image.open(BytesIO(stream[bmp_idx:])) as img:
                        img.load()
                        return img.convert("RGBA")
        return None
    except Exception:
        return None


def _load_max(source_path: Path) -> Image.Image:
    thumb = extract_max_thumbnail(source_path)
    if thumb is not None:
        return thumb
    raise RuntimeError(
        "This 3ds Max file has no embedded viewport thumbnail. "
        "In 3ds Max, enable 'Save Preview' in File Preferences, or export to .obj / .glb."
    )


def extract_f3d_thumbnail(path: Path) -> Image.Image | None:
    """Extract pre-rendered high-res PNG thumbnail from Autodesk Fusion 360 (.f3d) archives."""
    import zipfile
    try:
        with zipfile.ZipFile(str(path), "r") as zf:
            for name in zf.namelist():
                if "thumbnail" in name.lower() and name.lower().endswith((".png", ".jpg", ".jpeg")):
                    data = zf.read(name)
                    with Image.open(BytesIO(data)) as img:
                        img.load()
                        return img.convert("RGBA")
        return None
    except Exception:
        return None


def _load_f3d(source_path: Path) -> Image.Image:
    thumb = extract_f3d_thumbnail(source_path)
    if thumb is not None:
        return thumb
    raise RuntimeError("Could not find embedded preview thumbnail in this Fusion 360 (.f3d) file.")


def extract_maya_thumbnail(path: Path) -> Image.Image | None:
    """Extract embedded swatch/thumbnail from Autodesk Maya (.mb, .ma) files."""
    try:
        ext = path.suffix.lower()
        if ext == ".ma":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in range(500):
                    line = f.readline()
                    if not line:
                        break
                    if "thumbnail" in line.lower():
                        import base64
                        import re
                        m = re.search(r'["\']([A-Za-z0-9+/=]{100,})["\']', line)
                        if m:
                            try:
                                 raw = base64.b64decode(m.group(1))
                                 with Image.open(BytesIO(raw)) as img:
                                     img.load()
                                     return img.convert("RGBA")
                            except Exception:
                                pass
        elif ext == ".mb":
            with open(path, "rb") as f:
                header_data = f.read(512 * 1024)
                png_idx = header_data.find(b"\x89PNG\r\n\x1a\n")
                if png_idx >= 0:
                    with Image.open(BytesIO(header_data[png_idx:])) as img:
                        img.load()
                        return img.convert("RGBA")
                jpg_idx = header_data.find(b"\xff\xd8\xff")
                if jpg_idx >= 0:
                    with Image.open(BytesIO(header_data[jpg_idx:])) as img:
                        img.load()
                        return img.convert("RGBA")
        return None
    except Exception:
        return None


def _load_maya(source_path: Path) -> Image.Image:
    thumb = extract_maya_thumbnail(source_path)
    if thumb is not None:
        return thumb
    raise RuntimeError(
        "This Maya file has no embedded swatch thumbnail. "
        "In Maya, enable 'Save Thumbnail' in Scene Save Preferences, or export to .obj / .glb."
    )


def _load_cad_solid(source_path: Path, config: PreviewConfig) -> Image.Image:
    """Convert universal CAD solids (.step, .stp, .iges, .igs) into 3D meshes for 360° orbit preview."""
    try:
        import cascadio
        glb_bytes = cascadio.to_glb_bytes(str(source_path))
        import trimesh
        mesh = trimesh.load(BytesIO(glb_bytes), file_type="glb")
        if isinstance(mesh, trimesh.Scene):
            try:
                mesh = mesh.to_geometry()
            except Exception:
                mesh = trimesh.util.concatenate(mesh.dump())
        return render_3d_mesh(
            mesh=mesh,
            yaw_deg=config.yaw,
            pitch_deg=config.pitch,
            model_color=config.model_color,
        )
    except Exception as exc:
        raise RuntimeError(f"Could not convert CAD solid to 3D mesh: {exc}")


def load_source_image(source_path: Path, config: PreviewConfig | None = None) -> Image.Image:
    """Load an input file (2D images, PSD, 3D meshes, CAD files) into a verified RGBA PIL Image."""
    source_path = Path(source_path)
    ext = source_path.suffix.lower()

    if ext in (".svg", ".svgz"):
        return _load_svg(source_path)

    if ext == ".psd":
        return _load_psd(source_path)

    if ext == ".dxf":
        return _load_dxf(source_path)

    if ext == ".dwg":
        return _load_dwg(source_path)

    if ext == ".max":
        return _load_max(source_path)

    if ext == ".f3d":
        return _load_f3d(source_path)

    if ext in (".mb", ".ma"):
        return _load_maya(source_path)

    if ext in (".step", ".stp", ".iges", ".igs"):
        return _load_cad_solid(source_path, config or PreviewConfig())

    if ext in SUPPORTED_3D_EXTENSIONS:
        return _load_3d(source_path, config or PreviewConfig())

    # Standard raster formats (.png, .webp, .tif, .tiff)
    with Image.open(source_path) as img:
        if getattr(img, "is_animated", False):
            img.seek(0)
        img.load()
        if img.mode in ("CMYK", "YCbCr"):
            img = img.convert("RGB")
        return img.convert("RGBA")

def render_3d_mesh(
    mesh,
    yaw_deg: float = 45.0,
    pitch_deg: float = 30.0,
    model_color: tuple[int, int, int] = (120, 130, 160),
    target_dimension: int = 2400,
) -> Image.Image:
    """Render a 3D mesh from any yaw/pitch angle to a transparent RGBA PIL Image."""
    import numpy as np
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt, QPointF
    from PySide6.QtGui import QImage, QPainter, QColor, QPolygonF, QBrush

    # Center and scale to unit radius preserving exact submesh geometry
    verts = mesh.vertices - mesh.centroid
    max_radius = float(np.max(np.linalg.norm(verts, axis=1)))
    if max_radius > 0:
        verts = verts / max_radius

    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)

    Ry = np.array([
        [np.cos(yaw), 0, np.sin(yaw)],
        [0, 1, 0],
        [-np.sin(yaw), 0, np.cos(yaw)],
    ])
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(pitch), -np.sin(pitch)],
        [0, np.sin(pitch), np.cos(pitch)],
    ])
    R = Rx @ Ry

    v_rot = verts @ R.T
    n_rot = mesh.face_normals @ R.T

    # Painter's algorithm: sort faces by camera Z-depth
    face_z = v_rot[mesh.faces].mean(axis=1)[:, 2]
    order = np.argsort(face_z)

    # Gentle back-face culling to preserve thin vehicle panels and interior geometry
    visible_mask = n_rot[:, 2] > -0.55
    visible_order = [idx for idx in order if visible_mask[idx]]

    W, H = target_dimension, target_dimension
    scale = min(W, H) * 0.42
    pts_2d = v_rot[:, :2] * scale + np.array([W / 2, H / 2])

    # Directional Key Light + Ambient Light (two-sided diffuse so car interior/doors remain illuminated)
    light_dir = np.array([0.45, 0.65, 0.61])
    light_dir /= np.linalg.norm(light_dir)
    diffuse = np.abs(n_rot @ light_dir) * 0.72
    ambient = 0.35
    intensity = np.clip(ambient + diffuse, 0.0, 1.0)

    has_face_colors = (
        hasattr(mesh.visual, "face_colors")
        and mesh.visual.face_colors is not None
        and len(mesh.visual.face_colors) == len(mesh.faces)
    )

    qimg = QImage(W, H, QImage.Format.Format_ARGB32_Premultiplied)
    qimg.fill(Qt.GlobalColor.transparent)

    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    default_base = np.array(model_color, dtype=float)

    for idx in visible_order:
        face = mesh.faces[idx]
        if has_face_colors:
            base_c = mesh.visual.face_colors[idx][:3].astype(float)
        else:
            base_c = default_base

        lit = np.clip(base_c * intensity[idx], 0, 255).astype(int)
        painter.setBrush(QBrush(QColor(int(lit[0]), int(lit[1]), int(lit[2]), 255)))

        poly = QPolygonF([
            QPointF(pts_2d[face[0]][0], pts_2d[face[0]][1]),
            QPointF(pts_2d[face[1]][0], pts_2d[face[1]][1]),
            QPointF(pts_2d[face[2]][0], pts_2d[face[2]][1]),
        ])
        painter.drawPolygon(poly)

    painter.end()

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    qimg.save(buf, "PNG")
    buf.close()

    with Image.open(BytesIO(ba.data())) as pil_img:
        pil_img.load()
        return pil_img.convert("RGBA")


def extract_blend_thumbnail(path: Path) -> Image.Image | None:
    """Extract embedded preview thumbnail from a .blend file in pure Python without Blender."""
    import struct
    import gzip

    try:
        with open(path, "rb") as f:
            head = f.read(12)
            if head[:2] == b"\x1f\x8b":
                f.seek(0)
                gf = gzip.GzipFile(fileobj=f)
                head = gf.read(12)
                stream = gf
            else:
                stream = f

            if not head.startswith(b"BLENDER"):
                return None

            is_64_bit = (head[7:8] == b"-")
            is_big_endian = (head[8:9] == b"V")
            sizeof_bhead = 24 if is_64_bit else 20
            int_endian = ">i" if is_big_endian else "<i"

            REND = b"REND"
            TEST = b"TEST"

            while True:
                bhead = stream.read(sizeof_bhead)
                if len(bhead) < sizeof_bhead:
                    return None
                code = bhead[:4]
                length = struct.unpack(int_endian, bhead[4:8])[0]
                if code == REND:
                    stream.seek(length, 1)
                else:
                    break

            if code != TEST:
                return None

            dims = stream.read(8)
            if len(dims) < 8:
                return None
            w, h = struct.unpack(int_endian + "i", dims)
            length -= 8
            if length != w * h * 4 or w <= 0 or h <= 0:
                return None

            raw_rgba = stream.read(length)
            if len(raw_rgba) != length:
                return None

            img = Image.frombytes("RGBA", (w, h), raw_rgba)
            return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    except Exception:
        return None


def _load_3d(source_path: Path, config: PreviewConfig) -> Image.Image:
    """Load and render 3D formats (.obj, .gltf, .glb, .stl, .ply, .blend) into an RGBA PIL image."""
    ext = source_path.suffix.lower()

    if ext == ".blend":
        # 1. Zero-dependency extraction: read embedded scene thumbnail saved in the .blend file
        thumb = extract_blend_thumbnail(source_path)
        if thumb is not None:
            return thumb

        # 2. Fallback to local Blender binary if installed
        import shutil
        import subprocess
        import tempfile
        import sys

        blender_bin = shutil.which("blender")
        if not blender_bin and sys.platform == "win32":
            prog_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            foundation = prog_files / "Blender Foundation"
            if foundation.is_dir():
                matches = sorted(foundation.glob("Blender */blender.exe"))
                if matches:
                    blender_bin = str(matches[-1])
        elif not blender_bin and sys.platform == "darwin":
            mac_b = Path("/Applications/Blender.app/Contents/MacOS/blender")
            if mac_b.exists():
                blender_bin = str(mac_b)

        if blender_bin:
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_png = Path(tmp_dir) / "render.png"
                script = f"""
import bpy
bpy.context.scene.render.film_transparent = True
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.image_settings.color_mode = 'RGBA'
bpy.context.scene.render.filepath = r'{out_png}'
bpy.ops.render.render(write_still=True)
"""
                subprocess.run([blender_bin, "-b", str(source_path), "--python-expr", script], capture_output=True, timeout=60)
                if out_png.exists():
                    with Image.open(out_png) as img:
                        img.load()
                        return img.convert("RGBA")

        raise RuntimeError(
            "This .blend file has no embedded preview thumbnail. "
            "To preview it, either install Blender or export the model to .glb, .gltf, or .obj (which render natively with full 360° controls)!"
        )

    try:
        import trimesh
    except ImportError:
        raise RuntimeError("trimesh is required for 3D model preview generation. Run: pip install trimesh")

    loaded = trimesh.load(source_path)
    if isinstance(loaded, trimesh.Scene):
        if len(loaded.geometry) == 0:
            raise ValueError("3D Scene contains no valid geometry")
        try:
            mesh = loaded.to_geometry()
        except Exception:
            mesh = trimesh.util.concatenate(loaded.dump())
    else:
        mesh = loaded
    return render_3d_mesh(
        mesh=mesh,
        yaw_deg=config.yaw,
        pitch_deg=config.pitch,
        model_color=config.model_color,
    )


def generate_file(
    source_path: Path,
    output_path: Path,
    config: PreviewConfig | None = None,
    text: str | None = None,
) -> None:
    if config is None:
        config = PreviewConfig(text=text if text is not None else DEFAULT_TEXT)

    source = load_source_image(source_path, config)
    output = compose_preview(source, config)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        output.save(temp_path, format="JPEG", quality=96, subsampling=0, optimize=True)
        temp_path.replace(output_path)
    finally:
        temp_path.unlink(missing_ok=True)


def preview_jpeg_bytes(
    source_path: Path | str,
    config: PreviewConfig | None = None,
    text: str | None = None,
    max_dimension: int = 850,
) -> bytes:
    source_path = Path(source_path)
    if config is None:
        config = PreviewConfig(text=text if text is not None else DEFAULT_TEXT)

    source = load_source_image(source_path, config)
    w, h = source.size
    if max(w, h) > max_dimension:
        ratio = max_dimension / max(w, h)
        tw = max(100, round(w * ratio))
        th = max(100, round(h * ratio))
        source = source.resize((tw, th), Image.Resampling.BILINEAR)

    preview = compose_preview(source, config)

    buffer = BytesIO()
    preview.save(buffer, format="JPEG", quality=85, subsampling=0)
    return buffer.getvalue()

def process_folder(
    input_folder: Path,
    output_folder: Path,
    config: PreviewConfig,
    progress: Callable[[int, int, str], None],
    is_cancelled: Callable[[], bool],
) -> tuple[int, int, list[str]]:
    files = sorted(
        path for path in input_folder.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        ext_list = ", ".join(SUPPORTED_EXTENSIONS)
        raise ValueError(f"No supported images ({ext_list}) found in the input folder")

    output_folder.mkdir(parents=True, exist_ok=True)
    success = 0
    failed = 0
    errors: list[str] = []
    total = len(files)

    for index, source_path in enumerate(files, start=1):
        if is_cancelled():
            break
        if source_path.suffix.lower() == ".zip":
            import zipfile
            import tempfile
            import shutil

            zip_tmp = Path(tempfile.mkdtemp(prefix="previewgen_zip_"))
            try:
                with zipfile.ZipFile(source_path, "r") as zf:
                    for member in zf.infolist():
                        parts = Path(member.filename).parts
                        if any(part.startswith(".") or part == "__MACOSX" for part in parts):
                            continue
                        if member.is_dir() or member.filename.lower().endswith((".ds_store", "thumbs.db", "desktop.ini")):
                            continue
                        target = (zip_tmp / member.filename).resolve()
                        if not str(target).startswith(str(zip_tmp.resolve())):
                            continue
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)

                inner_files = sorted(
                    p for p in zip_tmp.rglob("*.*")
                    if p.is_file()
                    and p.suffix.lower() in SUPPORTED_EXTENSIONS
                    and p.suffix.lower() != ".zip"
                    and not any(part.startswith(".") or part == "__MACOSX" for part in p.parts)
                )
                if not inner_files:
                    failed += 1
                    errors.append(f"{source_path.name}: No supported files found inside archive")
                for inner in inner_files:
                    if is_cancelled():
                        break
                    try:
                        rel_parts = inner.relative_to(zip_tmp).parent.parts
                        if rel_parts:
                            folder_slug = "_".join(rel_parts)
                            out_name = f"{source_path.stem}_{folder_slug}_{inner.stem}.jpg"
                        else:
                            out_name = f"{source_path.stem}_{inner.stem}.jpg"
                        generate_file(inner, output_folder / out_name, config)
                        success += 1
                        status = f"Created {out_name}"
                    except Exception as exc:
                        failed += 1
                        errors.append(f"{source_path.name} -> {inner.name}: {exc}")
            finally:
                shutil.rmtree(zip_tmp, ignore_errors=True)
        else:
            try:
                generate_file(
                    source_path,
                    output_folder / f"{source_path.stem}.jpg",
                    config,
                )
                success += 1
                status = f"Created {source_path.stem}.jpg"
            except Exception as exc:
                failed += 1
                status = f"Failed {source_path.name}"
                errors.append(f"{source_path.name}: {exc}")

    return success, failed, errors
