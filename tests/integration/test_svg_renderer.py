from pathlib import Path
import sys
import tempfile
from PIL import Image
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Gracefully skip if resvg_py is not installed in the current environment
resvg_py = pytest.importorskip("resvg_py")

from processor import PreviewConfig, generate_file


def test_svg_dimension_preservation():
    """Verify that production SVGs with explicit dimensions preserve exact pixel dimensions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        svg_path = tmp / "test_icon.svg"
        out_jpg = tmp / "test_icon.jpg"

        svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">
            <rect width="1200" height="900" fill="none"/>
            <circle cx="600" cy="450" r="300" fill="#3B82F6"/>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        cfg = PreviewConfig()
        generate_file(svg_path, out_jpg, cfg)

        assert out_jpg.is_file()
        with Image.open(out_jpg) as out_img:
            assert out_img.size == (1200, 900), f"Expected output (1200, 900), got {out_img.size}"
