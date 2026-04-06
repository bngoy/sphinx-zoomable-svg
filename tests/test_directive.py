"""Tests for the zoomable-figure directive."""

import pytest
from pathlib import Path


@pytest.mark.sphinx("html", testroot="zoomable")
def test_zoomable_svg_produces_html(app, status, warning):
    """Test that the directive produces the expected HTML structure."""
    app.build()
    assert warning.getvalue() == ""

    content = (Path(app.outdir) / "index.html").read_text()

    # Check the container is present with correct attributes
    assert 'class="zoomable-container"' in content
    assert 'data-type="svg"' in content
    assert 'data-src="_images/sample.svg"' in content

    # Check controls are present
    assert 'class="zoomable-controls"' in content
    assert "zoomable-zoom-in" in content
    assert "zoomable-zoom-out" in content
    assert "zoomable-reset" in content
    assert "zoomable-fullscreen" in content

    # Check caption
    assert "<figcaption>" in content
    assert "This is a zoomable SVG figure" in content

    # Check legend
    assert "zoomable-legend" in content
    assert "This is the legend for the SVG figure" in content

    # Check JS and CSS are included
    assert "svg-pan-zoom.min.js" in content
    assert "zoomable-images.js" in content
    assert "zoomable-images.css" in content


@pytest.mark.sphinx("html", testroot="zoomable")
def test_image_copied_to_output(app, status, warning):
    """Test that the SVG image is copied to _images/ in the build output."""
    app.build()

    images_dir = Path(app.outdir) / "_images"
    assert (images_dir / "sample.svg").exists()


@pytest.mark.sphinx("html", testroot="zoomable")
def test_no_caption_figure(app, status, warning):
    """Test a figure without caption renders correctly."""
    app.build()
    content = (Path(app.outdir) / "index.html").read_text()

    # There should be at least two zoomable containers
    assert content.count('class="zoomable-container"') == 2


@pytest.mark.sphinx("html", testroot="zoomable")
def test_subdir_image_path_uses_relative_prefix(app, status, warning):
    """Test that a page in a subdirectory uses ../_images/ for the data-src."""
    app.build()

    content = (Path(app.outdir) / "subdir" / "page.html").read_text()
    assert 'data-src="../_images/subsample.svg"' in content

    # Also verify the image was copied
    assert (Path(app.outdir) / "_images" / "subsample.svg").exists()
