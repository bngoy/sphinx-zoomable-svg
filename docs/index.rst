sphinx-zoomable-images Examples
================================

This page demonstrates the ``zoomable-figure`` directive with various image
types and options. Try zooming with your mouse wheel, panning by clicking and
dragging, and using the overlay controls in the top-right corner of each figure.


SVG: Network Architecture Diagram
----------------------------------

A detailed network architecture diagram. Zoom in to read the labels on each
component.

.. zoomable-figure:: _static/images/network.svg
   :alt: Network architecture showing load balancers, web servers, app servers, and databases
   :caption: Figure 1 -- Multi-tier network architecture
   :width: 100%
   :height: 500px

   This diagram illustrates a typical multi-tier web application architecture
   with a load balancer distributing traffic across multiple web servers,
   application servers, a PostgreSQL database, and a Redis cache layer.


SVG: Request Processing Flowchart
----------------------------------

A flowchart showing HTTP request processing logic.

.. zoomable-figure:: _static/images/flowchart.svg
   :alt: Flowchart of HTTP request processing with authentication and validation
   :caption: Figure 2 -- Request processing flow
   :width: 100%
   :height: 550px


Raster Image: Bar Chart (PNG)
------------------------------

Raster images are also supported. They are wrapped in an SVG element internally
so that the same zoom and pan controls work.

.. zoomable-figure:: _static/images/chart.png
   :alt: Bar chart showing sample data
   :caption: Figure 3 -- Sample bar chart (PNG raster image)
   :width: 100%
   :height: 400px

   Note: raster images will pixelate when zoomed in, unlike SVGs which remain
   crisp at any zoom level.


Minimal Example
---------------

A figure with no caption, no legend, and default dimensions.

.. zoomable-figure:: _static/images/flowchart.svg
   :alt: Simple flowchart


Aligned Figure
--------------

A center-aligned figure with custom dimensions.

.. zoomable-figure:: _static/images/network.svg
   :alt: Network diagram
   :caption: Figure 4 -- Center-aligned figure
   :align: center
   :width: 80%
   :height: 400px
