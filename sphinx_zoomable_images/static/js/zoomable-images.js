/**
 * Zoomable Images - Sphinx extension for interactive pan/zoom on images.
 * Uses svg-pan-zoom library for SVG manipulation.
 */
(function () {
  "use strict";

  var PANZOOM_OPTIONS = {
    zoomEnabled: true,
    panEnabled: true,
    controlIconsEnabled: false,
    mouseWheelZoomEnabled: true,
    fit: true,
    center: true,
    minZoom: 0.1,
    maxZoom: 20,
    zoomScaleSensitivity: 0.3,
  };

  /**
   * Initialize a single zoomable container.
   */
  function initContainer(container) {
    var src = container.getAttribute("data-src");
    var type = container.getAttribute("data-type");
    var alt = container.getAttribute("data-alt") || "";

    if (type === "svg") {
      initSvgImage(container, src, alt);
    } else {
      initRasterImage(container, src, alt);
    }
  }

  /**
   * Fetch an SVG file and inline it into the container, then init pan-zoom.
   */
  function initSvgImage(container, src, alt) {
    fetch(src)
      .then(function (response) {
        if (!response.ok) throw new Error("Failed to load SVG: " + src);
        return response.text();
      })
      .then(function (svgText) {
        // Parse the SVG and insert it
        var parser = new DOMParser();
        var doc = parser.parseFromString(svgText, "image/svg+xml");
        var svgEl = doc.documentElement;

        // Ensure the SVG fills its container
        svgEl.setAttribute("width", "100%");
        svgEl.setAttribute("height", "100%");
        if (alt) svgEl.setAttribute("aria-label", alt);

        // Insert before controls
        var controls = container.querySelector(".zoomable-controls");
        container.insertBefore(svgEl, controls);

        // Initialize svg-pan-zoom
        var instance = svgPanZoom(svgEl, PANZOOM_OPTIONS);
        wireControls(container, instance, src, "svg");

        // Handle window resize
        window.addEventListener("resize", function () {
          instance.resize();
          instance.fit();
          instance.center();
        });
      })
      .catch(function (err) {
        console.error("zoomable-images:", err);
        container.innerHTML =
          '<p style="color:red">Failed to load SVG: ' + src + "</p>";
      });
  }

  /**
   * Create an SVG wrapper around a raster image and init pan-zoom.
   */
  function initRasterImage(container, src, alt) {
    var img = new Image();
    img.onload = function () {
      var w = img.naturalWidth;
      var h = img.naturalHeight;

      // Create an SVG that wraps the raster image
      var svgNS = "http://www.w3.org/2000/svg";
      var xlinkNS = "http://www.w3.org/1999/xlink";

      var svgEl = document.createElementNS(svgNS, "svg");
      svgEl.setAttribute("viewBox", "0 0 " + w + " " + h);
      svgEl.setAttribute("width", "100%");
      svgEl.setAttribute("height", "100%");
      if (alt) svgEl.setAttribute("aria-label", alt);

      // We need a <g> wrapper for svg-pan-zoom to work properly
      var g = document.createElementNS(svgNS, "g");

      var imageEl = document.createElementNS(svgNS, "image");
      imageEl.setAttributeNS(xlinkNS, "xlink:href", src);
      imageEl.setAttribute("href", src);
      imageEl.setAttribute("width", w);
      imageEl.setAttribute("height", h);

      g.appendChild(imageEl);
      svgEl.appendChild(g);

      // Insert before controls
      var controls = container.querySelector(".zoomable-controls");
      container.insertBefore(svgEl, controls);

      // Initialize svg-pan-zoom
      var instance = svgPanZoom(svgEl, PANZOOM_OPTIONS);
      wireControls(container, instance, src, "raster");

      window.addEventListener("resize", function () {
        instance.resize();
        instance.fit();
        instance.center();
      });
    };

    img.onerror = function () {
      console.error("zoomable-images: Failed to load image:", src);
      container.innerHTML =
        '<p style="color:red">Failed to load image: ' + src + "</p>";
    };

    img.src = src;
  }

  /**
   * Wire up control buttons to the svg-pan-zoom instance.
   */
  function wireControls(container, instance, src, type) {
    var zoomIn = container.querySelector(".zoomable-zoom-in");
    var zoomOut = container.querySelector(".zoomable-zoom-out");
    var reset = container.querySelector(".zoomable-reset");
    var fullscreen = container.querySelector(".zoomable-fullscreen");

    if (zoomIn) {
      zoomIn.addEventListener("click", function (e) {
        e.preventDefault();
        instance.zoomIn();
      });
    }

    if (zoomOut) {
      zoomOut.addEventListener("click", function (e) {
        e.preventDefault();
        instance.zoomOut();
      });
    }

    if (reset) {
      reset.addEventListener("click", function (e) {
        e.preventDefault();
        instance.resetZoom();
        instance.resetPan();
        instance.fit();
        instance.center();
      });
    }

    if (fullscreen) {
      fullscreen.addEventListener("click", function (e) {
        e.preventDefault();
        openFullscreen(src, type, container);
      });
    }
  }

  /**
   * Open a fullscreen page in a new window with the image and controls.
   */
  function openFullscreen(src, type, originalContainer) {
    // Get the svg-pan-zoom library source so we can inline it
    var scripts = document.querySelectorAll('script[src*="svg-pan-zoom"]');
    var svgPanZoomSrc = scripts.length > 0 ? scripts[0].src : "";

    // Build an absolute URL for the image
    var imgUrl = new URL(src, window.location.href).href;
    var libUrl = svgPanZoomSrc
      ? new URL(svgPanZoomSrc, window.location.href).href
      : "";

    // Get the current page's zoomable-images.js URL
    var zoomableScripts = document.querySelectorAll(
      'script[src*="zoomable-images"]'
    );
    var zoomableJsUrl = zoomableScripts.length > 0 ? zoomableScripts[0].src : "";
    if (zoomableJsUrl)
      zoomableJsUrl = new URL(zoomableJsUrl, window.location.href).href;

    // Get the CSS URL
    var cssLinks = document.querySelectorAll('link[href*="zoomable-images"]');
    var cssUrl = cssLinks.length > 0 ? cssLinks[0].href : "";
    if (cssUrl) cssUrl = new URL(cssUrl, window.location.href).href;

    var alt = originalContainer.getAttribute("data-alt") || "";

    var html = [
      "<!DOCTYPE html>",
      "<html>",
      "<head>",
      '<meta charset="utf-8">',
      "<title>Fullscreen View</title>",
      cssUrl ? '<link rel="stylesheet" href="' + cssUrl + '">' : "",
      "<style>",
      "  * { margin: 0; padding: 0; box-sizing: border-box; }",
      "  body { background: #1a1a1a; overflow: hidden; }",
      "  .zoomable-figure { margin: 0; }",
      "  .zoomable-container {",
      "    width: 100vw !important;",
      "    height: 100vh !important;",
      "    border: none !important;",
      "    border-radius: 0 !important;",
      "    background: #1a1a1a !important;",
      "  }",
      "</style>",
      "</head>",
      "<body>",
      '<figure class="zoomable-figure">',
      '  <div class="zoomable-container"',
      '    data-src="' + imgUrl + '"',
      '    data-type="' + type + '"',
      '    data-alt="' + alt + '">',
      '    <div class="zoomable-controls">',
      '      <button class="zoomable-btn zoomable-zoom-in" title="Zoom in">',
      '        <svg viewBox="0 0 24 24" width="18" height="18"><line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/></svg>',
      "      </button>",
      '      <button class="zoomable-btn zoomable-zoom-out" title="Zoom out">',
      '        <svg viewBox="0 0 24 24" width="18" height="18"><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/></svg>',
      "      </button>",
      '      <button class="zoomable-btn zoomable-reset" title="Reset view">',
      '        <svg viewBox="0 0 24 24" width="18" height="18"><path d="M17.65 6.35A7.96 7.96 0 0012 4C7.58 4 4.01 7.58 4.01 12S7.58 20 12 20c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="currentColor"/></svg>',
      "      </button>",
      "    </div>",
      "  </div>",
      "</figure>",
      libUrl ? '<script src="' + libUrl + '"></' + "script>" : "",
      zoomableJsUrl
        ? '<script src="' + zoomableJsUrl + '"></' + "script>"
        : "",
      "</body>",
      "</html>",
    ].join("\n");

    var win = window.open("", "_blank");
    if (win) {
      win.document.write(html);
      win.document.close();
    }
  }

  /**
   * Initialize all zoomable containers on the page.
   */
  function init() {
    var containers = document.querySelectorAll(".zoomable-container");
    for (var i = 0; i < containers.length; i++) {
      initContainer(containers[i]);
    }
  }

  // Run on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
