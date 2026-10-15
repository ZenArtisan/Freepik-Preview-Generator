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


@dataclass
class PreviewConfig:
    text: str = DEFAULT_TEXT
    position: str = "top-left"            # top-left, top-right, center, bottom-left, bottom-right
    opacity: float = 0.9                  # 0.0 to 1.0 (text opacity)
    invert_triangles: bool = True         # True: Left Solid, Right Transparent; False: Left Transparent, Right Solid
    solid_color: tuple[int, int, int] = (255, 255, 255)  # RGB of solid triangle
    text_color: tuple[int, int, int] = (255, 255, 255)   # RGB of text fill
    has_outline: bool = True              # Enable/disable outline stroke
    outline_color: tuple[int, int, int] = (0, 0, 0)      # RGB of outline stroke
    outline_thickness: int = 2            # 1 (thin) to 5 (extra bold)
    font_scale: float = 1.0               # 0.5 to 2.0


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
        raise ValueError("PNG has no transparent pixels")
    if alpha_max == 0:
        raise ValueError("PNG is completely transparent")

    bg = make_background(
        width,
        height,
        invert_triangles=config.invert_triangles,
        solid_color=config.solid_color,
    )
    result = Image.alpha_composite(bg, original)

    # Draw watermark only if text is non-empty
    label = config.text.strip()
    if label:
        base_font_size = round(min(width, height) * 0.038 * config.font_scale)
        font_size = max(14, min(240, base_font_size))
        font = _font(font_size)

        draw_calc = ImageDraw.Draw(result)
        box = draw_calc.textbbox((0, 0), label, font=font, stroke_width=0)
        text_size = (box[2] - box[0], box[3] - box[1])

        obj_bounds = original.getchannel("A").getbbox()
        x, y = _calculate_text_position(result.size, text_size, config.position, obj_bounds)

        # Draw text onto transparent overlay to apply opacity cleanly
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


def generate_file(
    source_path: Path,
    output_path: Path,
    config: PreviewConfig | None = None,
    text: str | None = None,
) -> None:
    if config is None:
        config = PreviewConfig(text=text if text is not None else DEFAULT_TEXT)

    with Image.open(source_path) as source:
        source.load()
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

    with Image.open(source_path) as source:
        source.load()
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
        if path.is_file() and path.suffix.lower() == ".png"
    )
    if not files:
        raise ValueError("No PNG files found in the input folder")

    output_folder.mkdir(parents=True, exist_ok=True)
    success = 0
    failed = 0
    errors: list[str] = []
    total = len(files)

    for index, source_path in enumerate(files, start=1):
        if is_cancelled():
            break
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
        progress(index, total, status)

    return success, failed, errors
