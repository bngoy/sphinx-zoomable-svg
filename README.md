# sphinx-zoomable-images

A Sphinx extension that provides a `zoomable-figure` directive for embedding interactive, zoomable and pannable images in your documentation.

Supports both SVG and raster images (PNG, JPG, etc.) with mouse wheel zoom, click-and-drag pan, overlay controls, and a fullscreen mode.

Powered by the [svg-pan-zoom](https://github.com/bumbu/svg-pan-zoom) library (BSD-2-Clause).

## Installation

```bash
pip install sphinx-zoomable-images
```

Or for development:

```bash
pipenv install --dev
pipenv shell
```

## Quick Start

Add the extension to your Sphinx `conf.py`:

```python
extensions = ["sphinx_zoomable_images"]
```

Then use the `zoomable-figure` directive in your reStructuredText files:

```rst
.. zoomable-figure:: images/architecture.svg
   :alt: System architecture diagram
   :caption: Figure 1 -- System architecture overview
   :width: 100%
   :height: 500px

   Optional legend content with additional details.
```

## Directive Reference

### `zoomable-figure`

```rst
.. zoomable-figure:: path/to/image
   :alt: Alt text for accessibility
   :caption: Caption displayed below the image
   :width: CSS width (e.g. 100%, 600px)
   :height: CSS height (e.g. 500px, 50vh)
   :align: left | center | right
   :class: additional-css-class

   Optional legend (body content parsed as reStructuredText).
```

**Argument:** Path to the image file, relative to the current document.

**Supported formats:** `.svg`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`

### Options

| Option     | Description                                      | Example       |
|------------|--------------------------------------------------|---------------|
| `:alt:`    | Alt text for accessibility                       | `A diagram`   |
| `:caption:`| Caption text shown below the image               | `Figure 1`    |
| `:width:`  | CSS width of the container                       | `100%`        |
| `:height:` | CSS height of the container                      | `500px`       |
| `:align:`  | Horizontal alignment                             | `center`      |
| `:class:`  | Additional CSS classes on the `<figure>` element | `my-figure`   |

If `:width:` and `:height:` are omitted, the container defaults to `width: 100%; height: 500px`.

## Interactive Controls

Each figure includes an overlay control panel (top-right corner) with:

| Control       | Action                                            |
|---------------|---------------------------------------------------|
| **+**         | Zoom in                                           |
| **-**         | Zoom out                                          |
| **Reset**     | Reset zoom level and re-center the image          |
| **Fullscreen**| Open the image in a new browser tab at full size  |

Additionally:
- **Mouse wheel** zooms in/out
- **Click and drag** pans the image

## How It Works

- **SVG images** are fetched and inlined into the DOM, then initialized with svg-pan-zoom for native vector zoom/pan.
- **Raster images** (PNG, JPG, etc.) are wrapped inside an SVG `<image>` element, allowing svg-pan-zoom to handle them uniformly.
- **Fullscreen** opens a new browser tab with a minimal page containing the image and controls at full viewport size.

## Development

### Setup

```bash
# Clone the repo
git clone https://github.com/bngoy/sphinx-zoomable-svg.git
cd sphinx-zoomable-svg

# Install with Pipenv (recommended)
pipenv install --dev
pipenv shell

# Or install directly
pip install -e ".[test]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Building the Reference Docs

The `docs/` directory contains reference examples demonstrating SVG, PNG, and various directive options:

```bash
sphinx-build -b html docs docs/_build
# Open docs/_build/index.html in a browser
```

The examples include:
- SVG network architecture diagram (detailed, multi-component)
- SVG request processing flowchart
- PNG raster bar chart
- Minimal figure (no caption/legend, default size)
- Center-aligned figure with custom dimensions

### Building the Test Docs

```bash
sphinx-build -b html tests/roots/test-zoomable /tmp/zoomable-build
```

## Project Structure

```
sphinx_zoomable_images/
  __init__.py              # Sphinx extension: directive + setup
  static/
    js/
      svg-pan-zoom.min.js  # Vendored svg-pan-zoom library (v3.6.1)
      zoomable-images.js   # Initialization, controls, fullscreen logic
    css/
      zoomable-images.css  # Container and controls styling
docs/
  conf.py                  # Reference docs Sphinx config
  index.rst                # Example gallery with all features
  _static/images/          # Sample SVG and PNG images
tests/
  conftest.py              # Pytest/Sphinx test fixtures
  test_directive.py        # Extension tests
  roots/test-zoomable/     # Test Sphinx project
```

## License

BSD-2-Clause. See [LICENSE](LICENSE).

The bundled [svg-pan-zoom](https://github.com/bumbu/svg-pan-zoom) library is also BSD-2-Clause licensed.
