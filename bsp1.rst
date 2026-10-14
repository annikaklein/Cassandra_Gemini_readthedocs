Example 1: Lake Constance
=========================

Description of Study Site
-------------------------

Lake Constance lies on the border of Austria, Germany and Switzerland and represents the
**turbid end** of the tested water clarity range. The study area covers the shallow western
sub-basin of the Untersee in front of Horn, Germany (AOI 6.38 km²; 8.988–9.020°E,
47.685–47.708°N).

- Continuous depth gradient with a distinct spit extending into the lake (Wessels et al., 2015);
  the monotonic slope keeps depth variation within a 30 m Landsat pixel small and minimises
  mixed pixels.
- Fine-sediment input from the Rhine keeps the water meso-oligotrophic with reduced
  transparency (Heege et al., 2004); Secchi depth 6–9 m.

.. todo:: Add study-site map (overview of Europe, zoom on Lake Constance with AOI, Horn, Constance and St. Gallen).

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

.. todo:: Step-by-step configuration (``data_source``, AOI, deep-water sunglint polygon, method settings) and screenshots.

Results
-------

Retrieval of Version 6 (*Cassandra Gemini*) within 0–10 m, N = 15 754 pixels:

.. list-table::
   :header-rows: 1

   * - R²
     - RMSE
     - MAE
     - Bias
   * - 0.68
     - 0.38 m
     - 0.24 m
     - −0.03 m

The characteristic V-shaped shallow platform at Horn is reproduced in extent and depth
gradient. Signed differences stay within ±0.2 m across most of the shallow platform; the
largest overestimations (up to ≈ +0.4 m in the displayed range, isolated pixels with
|Δz\ :sub:`B`| ≈ 5.6 m) occur at the deeper margins, beyond the red-band penetration depth
(transition at 3.50–3.93 m). Wave breaking and residual land–water mixed pixels along the
shoreline may contribute. See :doc:`results` for the full analysis.

.. todo:: Add the six-panel validation figure (reference, estimate, relative/signed/absolute difference, parity plot) and a link to the results dataset (DOI).
