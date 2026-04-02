# CLAUDE.md

Project guidelines for AI-assisted development.

## Project Overview

`sphinx-zoomable-images` is a Sphinx extension that provides a `zoomable-figure` directive. It renders images with interactive pan/zoom controls using the svg-pan-zoom JavaScript library.

## Tech Stack

- **Python** (>=3.11) -- Sphinx directive and extension plumbing
- **JavaScript** (ES5, no build step) -- Client-side zoom/pan/fullscreen logic
- **CSS** -- Control overlay and container styling
- **Sphinx** (>=9.0) -- Documentation framework this extension plugs into

## Project Structure

- `sphinx_zoomable_images/__init__.py` -- All Python code: directive class (`ZoomableFigure`), image copying hook, and `setup()` entry point
- `sphinx_zoomable_images/static/js/zoomable-images.js` -- JS initialization: fetches SVGs, wraps raster images in SVG, wires controls, handles fullscreen
- `sphinx_zoomable_images/static/js/svg-pan-zoom.min.js` -- Vendored third-party library (v3.6.1, BSD-2-Clause). Do not edit.
- `sphinx_zoomable_images/static/css/zoomable-images.css` -- All styles for the extension
- `tests/` -- Pytest test suite using `sphinx.testing` fixtures

## Development Commands

```bash
# Setup
pipenv install --dev
pipenv shell

# Run tests
pytest tests/ -v

# Lint and format
ruff check .
ruff format --check .

# Build reference docs (example gallery)
sphinx-build -b html docs docs/_build

# Build minimal test docs
sphinx-build -b html tests/roots/test-zoomable /tmp/zoomable-build

# Install in editable mode (alternative to pipenv)
pip install -e ".[test]"
```

## Key Conventions

- The extension outputs raw HTML via `nodes.raw` (not custom docutils nodes), keeping the implementation simple.
- Images are copied to `_build/_images/` via a `build-finished` event hook, since raw HTML nodes bypass Sphinx's built-in image collector.
- Static assets (JS/CSS) are injected via `html_static_path` manipulation at `builder-inited` time.
- The JS uses ES5 syntax (no transpilation needed) wrapped in an IIFE for compatibility.
- svg-pan-zoom.min.js is vendored (not loaded from CDN) so docs work offline.

## Testing

Tests use `sphinx.testing.fixtures` (`@pytest.mark.sphinx` decorator) to build real Sphinx projects and assert on the HTML output. Test roots are in `tests/roots/test-zoomable/`.

When adding a new directive option or behavior:
1. Add the option to `ZoomableFigure.option_spec`
2. Handle it in `ZoomableFigure.run()`
3. Add a usage example to `tests/roots/test-zoomable/index.rst`
4. Add assertions in `tests/test_directive.py`

## Supported Image Types

- SVG (`.svg`) -- fetched and inlined into DOM for native vector zoom
- Raster (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`) -- wrapped in SVG `<image>` element
