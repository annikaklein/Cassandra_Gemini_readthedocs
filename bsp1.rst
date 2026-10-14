Example 1: Lake Constance
=========================

Description of Study Site
-------------------------

Lake Constance lies on the border of Austria, Germany and Switzerland in central Europe and
represents the **turbid end** of the tested water clarity range. The study area covers the
shallow western basin of the Untersee in front of Horn, Germany (AOI 6.38 km²;
8.988–9.020°E, 47.685–47.708°N).

- Continuous depth gradient with a distinct spit extending into the lake (Wessels et al., 2015);
  the monotonic slope keeps depth variation within a 30 m Landsat pixel small and minimises
  intra-pixel spectral mixing.
- Continuous fine-sediment input from the Rhine keeps the water meso-oligotrophic with reduced
  optical transparency (Heege et al., 2004); Secchi depth 6–9 m.

.. figure:: _static/Study_Sites.png
   :width: 90%
   :align: center
   :alt: Study sites

   **Study sites.** Panels (a) and (b) show Lake Constance: (a) overview map of Europe with
   Lake Constance marked by an orange dot; (b) zoom into Lake Constance, with the nearby cities
   Constance (Germany) and St. Gallen (Switzerland) and the village Horn, in front of which the
   AOI (6.38 km²) covers the shallow western basin of the Untersee. Panels (c) and (d) show
   One Tree Reef (see :doc:`bsp2`).

Data
----

.. list-table::
   :widths: 30 70

   * - Satellite scene
     - Landsat 8 OLI, ``LC08_L2SP_194027_20140329_20200911_02_T1`` (29 March 2014, 10:10:49 UTC)
   * - Path / Row
     - 194 / 027
   * - Cloud cover / sun zenith
     - 3.56 % / 47.00°
   * - Reference bathymetry
     - Airborne LiDAR (29–30 March 2014), IGKB (2015), https://doi.org/10.1594/PANGAEA.855987
   * - Water level
     - 394.86 m NHN (Konstanz), 394.94 m NHN (Berlingen); 0.35 m below the 30-year mean
   * - Sunglint reference area
     - 0.004 km² open-water patch (9.024–9.033°E, 47.691–47.695°N)

Running the Pipeline
--------------------

The scene is retrieved via Google Earth Engine (``data_source = "gee"``).

1. Set the configuration cell:

   .. code-block:: python

      mission     = "Landsat"
      data_source = "gee"
      startdate   = "2014-03-20"
      enddate     = "2014-03-31"
      CX_METHOD   = "E1"
      CP_METHOD   = "A"
      AY_METHOD   = "A"

2. Authenticate with Google Earth Engine and draw the AOI on the map
   (8.988–9.020°E, 47.685–47.708°N), or enter the corner coordinates manually.
3. Select the scene ``LC08_L2SP_194027_20140329_20200911_02_T1`` from the previewed collection.
4. Draw the deep-water polygon for the sunglint correction
   (9.024–9.033°E, 47.691–47.695°N), or enter it manually.
5. Run the remaining cells (coefficients, water depth, TSM, Chl-a/CDOM, optimisation) and the
   export cell; the depth map is saved as ``zB.tif`` (see :doc:`code`).

.. todo:: Add screenshots of the configuration cell, the AOI map and the sunglint polygon.

Results
-------

Retrieval of Version 6 (*Cassandra Gemini*) within 0–10 m:

.. list-table::
   :header-rows: 1

   * - N
     - R²
     - RMSE
     - MAE
     - Bias
   * - 15 754
     - 0.68
     - 0.38 m
     - 0.24 m
     - −0.03 m

.. figure:: _static/LC_fig_combined_6panel_new2.png
   :width: 100%
   :align: center
   :alt: Validation Lake Constance

   **Comparison between estimated bathymetry (z\ :sub:`B,est`) and reference LiDAR bathymetry
   (z\ :sub:`B,ref`) for Lake Constance** within 0–10 m. (a) Reference and (b) estimated depth.
   (c) Relative difference δz\ :sub:`B` = (z\ :sub:`est` − z\ :sub:`ref`)/z\ :sub:`ref`,
   ranging from −86.1 % to +82.4 %. (d) Signed difference Δz\ :sub:`B` = z\ :sub:`est` −
   z\ :sub:`ref` (−5.60 m to +1.64 m); the colour scale is cropped at the 95th percentile of
   |Δz\ :sub:`B`|. (e) |Δz\ :sub:`B`| without cropping, revealing localised large errors at the
   deeper margins. Point colours in (f) correspond to |Δz\ :sub:`B`| as in (e); N = 15 754,
   R² = 0.68, RMSE = 0.38 m, MAE = 0.24 m, Bias = −0.03 m. Background imagery: © Google,
   © GeoBasis-DE/BKG.

The characteristic V-shaped shallow platform at Horn is reproduced in extent and depth
gradient, with the shallow nearshore zone (< 2 m) and the transition to deeper water (> 5 m)
visible in both maps. The relative difference lies mostly within ±50 %, with a slight
overestimation tendency; larger percentage deviations are confined to the deeper outer margins,
where small reference depths amplify the relative difference. Within the displayed range, Δz\ :sub:`B`
stays within ±0.2 m across the broad shallow area, with the largest positive residuals (up to
≈ +0.4 m) at the deeper margins at the tips of the platform. Isolated pixels with
|Δz\ :sub:`B`| ≈ 5.6 m at the northern tip lie beyond the red-band penetration depth
(transition at 3.50–3.93 m), where the inversion no longer retrieves depth reliably and
overestimates it. Small wind-driven breaking waves and residual land–water mixed pixels along the
Horn shoreline may contribute. In the parity plot (f) most points fall within ±1 m, and a
substantial fraction within ±0.5 m at shallow depths; deviations from the 1:1 line increase beyond
≈ 4 m. See :doc:`results` for the full analysis.

.. todo:: Add the link to the results dataset (DOI).
