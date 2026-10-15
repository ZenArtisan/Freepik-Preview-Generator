from __future__ import annotations

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
SUPPORTED_EXTENSIONS: tuple[str, ...] = (
    ".png",
    ".webp",
    ".tif",
    ".tiff",
    ".svg",
    ".svgz",
    ".psd",
    *SUPPORTED_3D_EXTENSIONS,
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
def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ):
        if path.exists():
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
    if alpha_min == 255:
        raise ValueError("Image has no transparent pixels (fully opaque)")
    if alpha_max == 0:
        raise ValueError("Image is completely transparent (empty canvas)")

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
        font = _font(font_size)

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


def load_source_image(source_path: Path, config: PreviewConfig | None = None) -> Image.Image:
    """Load an input file (.png, .webp, .tiff, .svg, .psd, 3D meshes) into a verified RGBA PIL Image."""
    ext = source_path.suffix.lower()

    if ext in (".svg", ".svgz"):
        return _load_svg(source_path)

    if ext == ".psd":
        return _load_psd(source_path)

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

    # Center and scale to unit radius
    verts = mesh.vertices - mesh.centroid
    max_radius = float(np.max(np.linalg.norm(verts, axis=1)))
    if max_radius > 0:
        verts = verts / max_radius

    # Decimate dense meshes to guarantee interactive 60fps orbit response
    if len(mesh.faces) > 16000:
        try:
            mesh = mesh.simplify_quadric_decimation(16000)
            verts = mesh.vertices - mesh.centroid
            max_r = float(np.max(np.linalg.norm(verts, axis=1)))
            if max_r > 0:
                verts = verts / max_r
        except Exception:
            pass

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

    # Back-face culling
    visible_mask = n_rot[:, 2] > -0.15
    visible_order = [idx for idx in order if visible_mask[idx]]

    W, H = target_dimension, target_dimension
    scale = min(W, H) * 0.42
    pts_2d = v_rot[:, :2] * scale + np.array([W / 2, H / 2])

    # Directional Key Light + Ambient Light
    light_dir = np.array([0.45, 0.65, 0.61])
    light_dir /= np.linalg.norm(light_dir)
    diffuse = np.maximum(0, n_rot @ light_dir)
    ambient = 0.32
    intensity = np.clip(ambient + 0.68 * diffuse, 0.0, 1.0)

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


def _load_3d(source_path: Path, config: PreviewConfig) -> Image.Image:
    """Load and render 3D formats (.obj, .gltf, .glb, .stl, .ply, .blend) into an RGBA PIL image."""
    ext = source_path.suffix.lower()

    if ext == ".blend":
        import shutil
        import subprocess
        import tempfile
        import sys

        blender_bin = shutil.which("blender")
        if not blender_bin and sys.platform == "win32":
            for p in (
                "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe",
                "C:/Program Files/Blender Foundation/Blender 4.1/blender.exe",
                "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
            ):
                if Path(p).exists():
                    blender_bin = p
                    break
        elif not blender_bin and sys.platform == "darwin":
            mac_b = Path("/Applications/Blender.app/Contents/MacOS/blender")
            if mac_b.exists():
                blender_bin = str(mac_b)

        if not blender_bin:
            raise RuntimeError(
                "Blender is required to render .blend files. Please install Blender, "
                "or export your model to .glb, .gltf, or .obj"
            )

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
            raise RuntimeError("Blender headless rendering failed to produce output image.")

    try:
        import trimesh
    except ImportError:
        raise RuntimeError("trimesh is required for 3D model preview generation. Run: pip install trimesh")

    loaded = trimesh.load(source_path)
    if isinstance(loaded, trimesh.Scene):
        if len(loaded.geometry) == 0:
            raise ValueError("3D Scene contains no valid geometry")
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
    source_path: Path,
    config: PreviewConfig | None = None,
    text: str | None = None,
) -> bytes:
    if config is None:
        config = PreviewConfig(text=text if text is not None else DEFAULT_TEXT)

    source = load_source_image(source_path, config)
    preview = compose_preview(source, config)

    buffer = BytesIO()
    preview.save(buffer, format="JPEG", quality=90, subsampling=0)
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
                        target = (zip_tmp / member.filename).resolve()
                        if not str(target).startswith(str(zip_tmp.resolve())):
                            continue
                        if member.is_dir() or member.filename.startswith("__MACOSX") or Path(member.filename).name.startswith("."):
                            continue
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)

                inner_files = sorted(
                    p for p in zip_tmp.rglob("*.*")
                    if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and p.suffix.lower() != ".zip"
                )
                if not inner_files:
                    failed += 1
                    errors.append(f"{source_path.name}: No supported files found inside archive")
                for inner in inner_files:
                    if is_cancelled():
                        break
                    try:
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
