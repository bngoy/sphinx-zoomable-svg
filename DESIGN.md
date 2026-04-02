# Design Document

## 1. Problem Statement

Sphinx's built-in `figure` and `image` directives render static images. For documentation that includes detailed diagrams (architecture diagrams, flowcharts, schematics), readers often need to zoom into specific areas or pan across large images. There is no native Sphinx support for this.

The goal is to provide a `zoomable-figure` directive that behaves like `figure` but renders images with interactive pan, zoom, and fullscreen capabilities -- directly in the HTML output, with no external services required.

## 2. Requirements (from initial discussion)

1. **Directive** similar to Sphinx's `figure`, supporting captions and legends
2. **Zoom** via mouse scroll wheel and overlay controls
3. **Pan** via click-and-drag
4. **Reset** control to re-center the image and reset zoom
5. **Fullscreen** mode opening a new page with the image at full viewport size
6. **SVG and raster support** -- both `.svg` and raster formats (`.png`, `.jpg`, etc.)
7. **Offline-capable** -- no CDN dependencies, everything bundled

## 3. Architecture Overview

The extension has three layers:

```
┌─────────────────────────────────────────────┐
│  Python (Sphinx directive)                  │
│  Generates HTML structure + data attributes │
├─────────────────────────────────────────────┤
│  JavaScript (client-side)                   │
│  Fetches/wraps images, inits svg-pan-zoom,  │
│  wires controls, handles fullscreen         │
├─────────────────────────────────────────────┤
│  CSS (styling)                              │
│  Container layout, control overlay, cursor  │
└─────────────────────────────────────────────┘
```

The Python layer runs at Sphinx build time and produces static HTML. The JavaScript layer runs in the browser when the built documentation is opened. This clean separation means the extension has zero impact on non-HTML builders.

## 4. Key Design Decisions

### 4.1. Raw HTML via `nodes.raw` (not custom docutils nodes)

**Decision:** The directive emits raw HTML through `nodes.raw` rather than defining custom docutils node classes with visitor functions.

**Rationale:** Custom nodes (`class zoomable_figure(nodes.General, nodes.Element)`) with `visit_`/`depart_` HTML translator methods are the "proper" docutils approach. However, they introduce significant complexity:
- Must register visitors for every builder (HTML, LaTeX, text) even if only HTML is relevant
- Must handle image URI resolution manually through `self.builder.images` and `self.builder.imgpath`
- Must coordinate with Sphinx's `ImageCollector` by keeping `nodes.image` children, then removing them in `doctree-resolved` to avoid double rendering
- Fragile across Sphinx versions as translator internals change

Raw HTML keeps the implementation to a single file with straightforward string assembly. The trade-off is that the directive only produces output for HTML builders, which is acceptable since interactive zoom/pan is inherently a browser feature.

### 4.2. Manual image copying via `build-finished` hook

**Decision:** Images referenced by `zoomable-figure` are copied to `_images/` by a `build-finished` event handler, not by Sphinx's built-in `ImageCollector`.

**Rationale:** Sphinx's `ImageCollector` walks the doctree looking for `nodes.image` nodes to register images for copying. Since we use `nodes.raw` (decision 4.1), there are no `nodes.image` nodes in the tree, and Sphinx never sees our images. Rather than inserting hidden `nodes.image` nodes just to trigger the collector (which adds complexity and couples us to collector internals), we track images ourselves in a module-level dict (`_pending_images`) and copy them in the `build-finished` hook. This is explicit, simple, and independent of Sphinx's image pipeline.

### 4.3. Unified SVG wrapper for raster images

**Decision:** Raster images (PNG, JPG, etc.) are wrapped inside an SVG `<image>` element at runtime, so svg-pan-zoom can handle both SVGs and rasters uniformly.

**Alternatives considered:**
- **CSS transforms** (scale + translate) for raster, svg-pan-zoom for SVG -- two separate code paths, divergent behavior
- **A different pan-zoom library** that natively handles raster -- adds another dependency, less mature options

**Rationale:** By wrapping raster images in `<svg><g><image href="..."/></g></svg>` with a `viewBox` matching the image's natural dimensions, svg-pan-zoom treats it identically to a native SVG. This gives a single code path in JavaScript -- same initialization, same controls, same API. The `<g>` wrapper is required because svg-pan-zoom manipulates the first `<g>` child for transform operations.

**Trade-off:** Raster images pixelate when zoomed (unlike SVGs which remain crisp). This is inherent to raster formats and documented in the README.

### 4.4. Fetch-and-inline for SVG files

**Decision:** SVG files are fetched via `fetch()` and inlined into the DOM, rather than loaded via `<object>`, `<embed>`, or `<img>` tags.

**Rationale:** svg-pan-zoom requires direct DOM access to the SVG element. `<img>` encapsulates the SVG and blocks all DOM access. `<object>` creates a separate document context that requires `contentDocument` access (blocked by same-origin policy in some setups). Fetching the SVG text and inserting it directly into the page DOM gives svg-pan-zoom full access. The SVG's `width`/`height` are set to `100%` so it fills the container.

**Trade-off:** `fetch()` doesn't work from `file://` URLs (CORS restriction). Users need a local HTTP server to preview docs locally, which is standard practice for Sphinx HTML output anyway.

### 4.5. Vendored svg-pan-zoom library

**Decision:** The svg-pan-zoom library (v3.6.1, BSD-2-Clause) is vendored in `static/js/svg-pan-zoom.min.js` rather than loaded from a CDN.

**Rationale:** Documentation must work offline -- on internal networks, in air-gapped environments, or simply when opened from disk. A CDN dependency would break these use cases. The library is 30KB minified, making the size impact negligible. The BSD-2-Clause license is compatible with any project.

### 4.6. Custom control overlay (not svg-pan-zoom's built-in controls)

**Decision:** We render our own control buttons (zoom in, zoom out, reset, fullscreen) rather than using svg-pan-zoom's `controlIconsEnabled: true`.

**Rationale:** svg-pan-zoom's built-in controls are SVG elements injected inside the SVG itself. They don't support our fullscreen feature, can't be styled with CSS independently, and their appearance varies across SVGs. Our HTML buttons sit in a `<div>` overlay positioned absolutely over the container, giving full CSS control (backdrop blur, hover states, transitions) and making it trivial to add the fullscreen button.

The control icons are inline SVGs (not icon fonts or images) for crisp rendering at any size without additional asset loading.

### 4.7. Fullscreen via `window.open()` with `document.write()`

**Decision:** The fullscreen button opens a new browser tab and writes a self-contained HTML page into it.

**Alternatives considered:**
- **Fullscreen API** (`element.requestFullscreen()`) -- requires user gesture, inconsistent across browsers, doesn't give a clean full-page layout
- **Modal overlay** on the same page -- conflicts with page scroll, z-index issues with Sphinx themes, complex to dismiss

**Rationale:** `window.open()` gives a clean, isolated full-viewport experience. The new page includes the same CSS, svg-pan-zoom library, and initialization JS (referenced by absolute URL from the original page's `<script>` and `<link>` tags). The dark background (`#1a1a1a`) provides contrast for diagrams. The fullscreen page omits the fullscreen button itself (since you're already fullscreen) but keeps zoom/pan controls.

### 4.8. Static assets via `html_static_path` manipulation

**Decision:** The extension's static directory is appended to `html_static_path` at `builder-inited` time, and JS/CSS files are registered via `app.add_js_file()` / `app.add_css_file()`.

**Rationale:** This is the standard Sphinx extension pattern for bundling assets. Sphinx copies the static directory contents into `_static/` in the build output. The `add_js_file`/`add_css_file` calls ensure the `<script>` and `<link>` tags appear in every page's `<head>`. The `builder-inited` event is the correct hook because `html_static_path` must be set before Sphinx begins copying files.

### 4.9. ES5 JavaScript in an IIFE

**Decision:** The JavaScript uses ES5 syntax wrapped in an immediately-invoked function expression (IIFE), with no build step or transpilation.

**Rationale:** Sphinx documentation is often viewed in enterprise environments with constrained browser versions. ES5 ensures maximum compatibility. The IIFE prevents any variables from leaking into the global scope. No build step means contributors can edit the JS directly without needing Node.js tooling. The only modern API used is `fetch()`, which is supported in all browsers that also support the CSS features we use (flexbox, backdrop-filter).

### 4.10. VERSION file as single source of truth

**Decision:** Package version is defined in a plain-text `VERSION` file at the repo root, read dynamically by `pyproject.toml` (via `[tool.setuptools.dynamic]`) and by `__init__.py` (via `importlib.metadata` with fallback to file read).

**Rationale:** A single source of truth prevents version drift between the package metadata and the runtime version string. The `VERSION` file is human-readable and trivially parseable by CI scripts (the release workflow reads it with `cat VERSION`). The dual read strategy in `__init__.py` handles both installed packages (where `importlib.metadata` works) and development installs (where the `VERSION` file is accessible on disk).

## 5. Data Flow

### Build time (Python/Sphinx)

```
RST source
  │
  ▼
ZoomableFigure.run()
  ├── Resolves image path relative to document
  ├── Validates file exists and format is supported
  ├── Registers image in _pending_images dict
  ├── Generates <figure> HTML with data attributes
  ├── Parses body content as legend (nested RST)
  └── Returns [nodes.raw, nodes.container]
          │
          ▼
      Sphinx build
          │
          ▼
  _copy_images() [build-finished hook]
  └── Copies images from source to _build/_images/
```

### Runtime (JavaScript/browser)

```
Page load
  │
  ▼
DOMContentLoaded
  │
  ▼
Find all .zoomable-container elements
  │
  ├── data-type="svg"           ├── data-type="raster"
  │   fetch(data-src)           │   new Image()
  │   DOMParser → inline SVG    │   Create <svg><g><image></g></svg>
  │       │                     │       │
  │       ▼                     │       ▼
  └───── svgPanZoom(svgEl, options) ────┘
              │
              ▼
        wireControls()
        ├── zoom-in    → instance.zoomIn()
        ├── zoom-out   → instance.zoomOut()
        ├── reset      → resetZoom + resetPan + fit + center
        └── fullscreen → window.open() with self-contained page
```

## 6. File Responsibilities

| File | Role |
|------|------|
| `__init__.py` | All Python code: directive class, image copy hook, `setup()` |
| `zoomable-images.js` | All client-side logic: init, fetch/wrap, controls, fullscreen |
| `svg-pan-zoom.min.js` | Vendored third-party library. **Do not edit.** |
| `zoomable-images.css` | All styling: container, controls, caption, legend |
| `VERSION` | Single source of truth for package version |

The deliberate choice to keep each layer in a single file (one Python module, one JS file, one CSS file) reflects the extension's focused scope. There is no benefit to splitting into multiple modules at this size.

## 7. HTML Output Structure

Each `zoomable-figure` directive produces:

```html
<figure class="zoomable-figure [align-X] [custom-class]">
  <div class="zoomable-container" id="zoomable-N"
       data-src="_images/file.svg" data-type="svg|raster"
       data-alt="..." style="width: ...; height: ...">
    <!-- JS inserts the SVG element here at runtime -->
    <div class="zoomable-controls">
      <button class="zoomable-btn zoomable-zoom-in">...</button>
      <button class="zoomable-btn zoomable-zoom-out">...</button>
      <button class="zoomable-btn zoomable-reset">...</button>
      <button class="zoomable-btn zoomable-fullscreen">...</button>
    </div>
  </div>
  <figcaption>Caption text</figcaption>  <!-- if :caption: set -->
</figure>
<div class="zoomable-legend">            <!-- if body content -->
  <p>Legend text (parsed RST)</p>
</div>
```

The container starts empty (no image visible). JavaScript populates it after the page loads. This is a deliberate trade-off: no-JS fallback shows an empty box, but the extension's entire value proposition is interactivity, which requires JS.

## 8. CI/CD Pipeline

```
PR opened/updated
  ├── tests.yml   → pytest on Python 3.11, 3.12, 3.13
  └── lint.yml    → ruff check + ruff format --check

PR merged to main
  └── release.yml
      ├── Read VERSION file
      ├── Check if git tag vX.Y.Z exists
      │   (if tag exists → skip everything)
      ├── Run tests on 3.11, 3.12, 3.13
      ├── Create git tag + GitHub Release
      └── Build + publish to PyPI
```

To release: bump the version in `VERSION`, merge to main. The pipeline handles tagging, GitHub release creation, and PyPI publishing automatically.
