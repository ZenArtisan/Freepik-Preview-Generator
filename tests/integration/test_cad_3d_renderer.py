from pathlib import Path
import sys
import tempfile
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from processor import PreviewConfig, generate_file


def test_3d_mesh_rendering_integration():
    """Verify 3D GLB mesh preview generation."""
    trimesh = pytest.importorskip("trimesh")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        glb_path = tmp / "model.glb"
        out_jpg = tmp / "model.jpg"

        mesh = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
        mesh.export(glb_path)

        cfg = PreviewConfig()
        generate_file(glb_path, out_jpg, cfg)

        assert out_jpg.is_file()
        assert out_jpg.stat().st_size > 0


def test_dxf_rendering_integration():
    """Verify AutoCAD DXF drawing preview generation."""
    ezdxf = pytest.importorskip("ezdxf")
    matplotlib = pytest.importorskip("matplotlib")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        dxf_path = tmp / "plan.dxf"
        out_jpg = tmp / "plan.jpg"

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_circle((0, 0), radius=50)
        msp.add_line((-50, -50), (50, 50))
        doc.saveas(dxf_path)

        cfg = PreviewConfig()
        generate_file(dxf_path, out_jpg, cfg)

        assert out_jpg.is_file()
        assert out_jpg.stat().st_size > 0
