from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_frontend_bundle_discovery():
    """Verify that frontend/dist/index.html is valid when built."""
    dist_html = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    if not dist_html.is_file():
        pytest.skip("Frontend has not been compiled yet. Run 'npm run build' in frontend/ to generate it.")

    content = dist_html.read_text(encoding="utf-8")
    assert '<div id="root">' in content
    assert "<script" in content
