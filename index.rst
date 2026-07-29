.. SDB documentation master file, created by
   sphinx-quickstart on Thu Jun 26 13:17:44 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Cassandra Gemini's documentation!
=============================================

Coastal bathymetry — the mapping of water depth in nearshore and inland
waters — is foundational to coastal management, flood modelling and
adaptation planning. Yet large stretches of the world's shallow coasts
remain uncharted: traditional ship-based surveys are slow, expensive and
operationally constrained in the very zones that matter most.

**Cassandra Gemini** addresses this gap. It is an open, physics-based
inversion framework for **Satellite-Derived Bathymetry (SDB)** that
recovers water depth — along with Total Suspended Matter, Phytoplankton
Chlorophyll-a and Coloured Dissolved Organic Matter — from a single
multispectral Landsat 8 scene, without requiring any in-situ depth
measurements for calibration.

Rather than fitting statistical relationships to field data, the framework
inverts the radiative transfer equation that governs how sunlight
propagates through the water column and reflects off the seabed. This
makes its results physically interpretable, independently reproducible
and open to community inspection.

Two worked examples are provided to guide you through the pipeline,
covering contrasting water clarity conditions:

- **Lake Constance** — a temperate meso-oligotrophic lake turbid with
  Rhine sediment
- **One Tree Reef, Great Barrier Reef** — a wave-exposed tropical reef
  in clear oceanic water

This documentation covers the theoretical background, the processing
workflow, and a step-by-step guide to running the pipeline in
``SDB.ipynb``.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tes
   methods
   code
   bsp1
   bsp2
   citations.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
