"""Sphinx extension providing a zoomable-figure directive with pan, zoom, and fullscreen."""

from __future__ import annotations

import os
import posixpath
import shutil
from pathlib import Path
from typing import Any, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("sphinx-zoomable-images")
except Exception:
    __version__ = (Path(__file__).parent.parent / "VERSION").read_text().strip()

SVG_EXTENSIONS = {".svg"}
RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
SUPPORTED_EXTENSIONS = SVG_EXTENSIONS | RASTER_EXTENSIONS

# Track images that need to be copied during build
_pending_images: dict[str, str] = {}  # basename -> absolute source path


class ZoomableFigure(SphinxDirective):
    """Directive for a zoomable, pannable figure with fullscreen support.

    Usage::

        .. zoomable-figure:: path/to/image.svg
           :alt: Description of the image
           :caption: My figure caption
           :width: 100%
           :height: 500px

           Optional legend content here.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec: ClassVar[dict[str, Any]] = {
        "alt": directives.unchanged,
        "caption": directives.unchanged,
        "width": directives.unchanged,
        "height": directives.unchanged,
        "align": lambda arg: directives.choice(arg, ("left", "center", "right")),
        "class": directives.class_option,
    }

    def run(self) -> list[nodes.Node]:
        image_path = self.arguments[0]
        ext = os.path.splitext(image_path)[1].lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise self.error(
                f"Unsupported image format '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        image_type = "svg" if ext in SVG_EXTENSIONS else "raster"

        env = self.env
        rel_filename, filename = env.relfn2path(image_path)
        env.note_dependency(rel_filename)

        if not os.path.isfile(filename):
            raise self.error(f"Image file not found: {filename}")

        # Track this image for copying during build
        basename = os.path.basename(rel_filename)
        _pending_images[basename] = filename

        # The image URL in the built output
        image_url = posixpath.join("_images", basename)

        # Build HTML
        container_id = f"zoomable-{env.new_serialno('zoomable')}"

        # Style attributes
        styles = []
        if "width" in self.options:
            styles.append(f"width: {self.options['width']}")
        if "height" in self.options:
            styles.append(f"height: {self.options['height']}")
        style_attr = f' style="{"; ".join(styles)}"' if styles else ""

        # CSS classes
        classes = ["zoomable-figure"]
        if "align" in self.options:
            classes.append(f"align-{self.options['align']}")
        if "class" in self.options:
            classes.extend(self.options["class"])
        class_attr = f' class="{" ".join(classes)}"'

        alt = self.options.get("alt", "")
        caption = self.options.get("caption", "")

        # Build the raw HTML for the interactive container
        html_parts = [
            f'<figure{class_attr}>',
            f'  <div class="zoomable-container" id="{container_id}"'
            f' data-src="{image_url}" data-type="{image_type}"'
            f' data-alt="{alt}"{style_attr}>',
            f'    <div class="zoomable-controls">',
            f'      <button class="zoomable-btn zoomable-zoom-in" title="Zoom in">',
            f'        <svg viewBox="0 0 24 24" width="18" height="18"><line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/></svg>',
            f'      </button>',
            f'      <button class="zoomable-btn zoomable-zoom-out" title="Zoom out">',
            f'        <svg viewBox="0 0 24 24" width="18" height="18"><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/></svg>',
            f'      </button>',
            f'      <button class="zoomable-btn zoomable-reset" title="Reset view">',
            f'        <svg viewBox="0 0 24 24" width="18" height="18"><path d="M17.65 6.35A7.96 7.96 0 0012 4C7.58 4 4.01 7.58 4.01 12S7.58 20 12 20c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="currentColor"/></svg>',
            f'      </button>',
            f'      <button class="zoomable-btn zoomable-fullscreen" title="Open fullscreen">',
            f'        <svg viewBox="0 0 24 24" width="18" height="18"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor"/></svg>',
            f'      </button>',
            f'    </div>',
            f'  </div>',
        ]

        if caption:
            html_parts.append(f"  <figcaption>{caption}</figcaption>")

        html_parts.append("</figure>")

        html = "\n".join(html_parts)
        raw_node = nodes.raw("", html, format="html")

        result_nodes: list[nodes.Node] = [raw_node]

        # If there's body content (legend), render it inside a container after the figure
        if self.content:
            legend_container = nodes.container(classes=["zoomable-legend"])
            self.state.nested_parse(self.content, self.content_offset, legend_container)
            result_nodes.append(legend_container)

        return result_nodes


def _copy_images(app: Sphinx, exception: Exception | None) -> None:
    """Copy zoomable images to the build output _images/ directory."""
    if exception:
        return
    if not hasattr(app.builder, "outdir"):
        return

    images_dir = Path(app.builder.outdir) / "_images"
    images_dir.mkdir(parents=True, exist_ok=True)

    for basename, src_path in _pending_images.items():
        dst = images_dir / basename
        if not dst.exists():
            shutil.copy2(src_path, dst)

    _pending_images.clear()


def _on_builder_inited(app: Sphinx) -> None:
    """Add the extension's static directory to Sphinx's static path."""
    static_dir = str(Path(__file__).parent / "static")
    if static_dir not in app.config.html_static_path:
        app.config.html_static_path.append(static_dir)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("zoomable-figure", ZoomableFigure)

    # Register static files
    app.connect("builder-inited", _on_builder_inited)
    app.connect("build-finished", _copy_images)
    app.add_js_file("js/svg-pan-zoom.min.js")
    app.add_js_file("js/zoomable-images.js")
    app.add_css_file("css/zoomable-images.css")

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
