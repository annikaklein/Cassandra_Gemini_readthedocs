Example 2: One Tree Reef
========================

Description of Study Site
-------------------------

One Tree Reef (≈ 23.5°S, 152°E) is a wave-exposed coral reef on the southern Great Barrier
Reef and represents the **clear end** of the tested range. The platform is named after One Tree
Island, the rubble cay in its lagoon; since the entire reef system is studied
(AOI 27.88 km²; 152.036–152.101°E, 23.478–23.516°S), the designation *One Tree Reef* is used.

- Oligotrophic oceanic water, Secchi depth ≈ 15 m.
- Swell from the east-southeast (mean significant wave height 1.7 m, mean peak period 5.8 s);
  wave breaking along the reef crest creates white-water that degrades the bottom signal on the
  exposed eastern and southern margins.
- Three geomorphic zones (Harris et al., 2023): steep fore-reef slope; near-horizontal reef flat
  (< 2 m); almost flat sandy lagoon floor deepening to basins of up to 13 m.
- Spur-and-groove systems on all margins (spurs 3–12 m, grooves 2–10 m wide) and a network of
  reticulate patch reefs with near-vertical walls ("The Labyrinth", coral heads 5–30 m,
  micro-channels < 5 m).

.. todo:: Add study-site map (overview of Australia, zoom on One Tree Reef with AOI and Gladstone).

Data
----

.. list-table::
   :widths: 30 70

   * - Satellite scene
     - Landsat 8 OLI, ``LC08_L2SP_090076_20181009_20200830_02_T2`` (9 October 2018, 23:47:10 UTC)
   * - Path / Row
     - 090 / 076
   * - Cloud cover / sun zenith
     - 4.57 % / 31.02°
   * - Reference bathymetry
     - Airborne LiDAR (8 October 2018), Harris et al. (2023), https://doi.org/10.1594/PANGAEA.963918
   * - Benchmark product
     - EOMAP WATCOR-X (Sentinel-2 mosaics, 15 May 2017–22 October 2018), GBRMPA Reef GeoHub
   * - Tidal height
     - 0.149 m MSL (FES2022 correction)
   * - Sunglint reference area
     - 0.011 km² open-water patch (152.057–152.062°E, 23.485–23.487°S)

Running the Pipeline
--------------------

.. todo:: Step-by-step configuration (local mode, ``mndwi_threshold = 0.25``) and screenshots.

Results
-------

Retrieval of Version 6 (*Cassandra Gemini*) within 0–10 m, N = 13 192 pixels:

.. list-table::
   :header-rows: 1

   * - R²
     - RMSE
     - MAE
     - Bias
   * - 0.54
     - 0.79 m
     - 0.58 m
     - −0.05 m

The shallow reef platform and surrounding deeper water are reproduced; gaps in the estimate
correspond to depths beyond the 10 m retrieval limit. Depth is overestimated at the outer reef
rim and around the island and the channel networks (sub-pixel structure, mixed pixels, wave
breaking) and slightly underestimated across the inner reef. The error transition depth is
4.92–6.38 m. See :doc:`results` for the comparison with the EOMAP product.

.. todo:: Add the six-panel validation figure and a link to the results dataset (DOI).
