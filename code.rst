Code Application
================

CassandraGemini.ipynb
---------

Configuration
~~~~~~~~~~~~~

Before running the pipeline, all user-defined parameters must be set
in the configuration cell. The pipeline follows the processing structure
described in :doc:`methods`, proceeding from preprocessing through water depth
estimation, water constituent retrieval, and parameter optimisation. Water level
correction is applied externally afterwards.

Quick Start
^^^^^^^^^^^

.. code-block:: python

   mission      = "Landsat"
   data_source  = "gee"          # or "local"
   startdate    = "2014-03-20"
   enddate      = "2014-03-31"
   TARGET_SCALE = 30
   PLOT_BANDS   = True
   CX_METHOD    = "E1"           # TSM:   "A" | "E1" | "E2"
   CP_METHOD    = "A"            # Chl-a: "A" | "E1" | "E2"
   AY_METHOD    = "A"            # CDOM:  "A" | "E1" | "E2"

Parameters
^^^^^^^^^^

``mission``
"""""""""""

Satellite mission to use.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``"Landsat"``
     - Landsat 8 OLI (currently the only supported mission)

----

``data_source``
"""""""""""""""

Defines how satellite imagery is loaded.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``"gee"``
     - Retrieve imagery via the Google Earth Engine API
   * - ``"local"``
     - Load locally stored image files

----

``startdate`` / ``enddate``
"""""""""""""""""""""""""""

Date range for image search. Only relevant if ``data_source == "gee"``.
Format: ``YYYY-MM-DD``

----

``TARGET_SCALE``
""""""""""""""""

Target pixel size in metres. Images are resampled to this resolution
via bilinear interpolation.

**Default:** ``30`` (native Landsat 8 OLI resolution)

----

``PLOT_BANDS``
""""""""""""""

If ``True``, intermediate processing steps and band results are
displayed as plots.

**Default:** ``True``

----

``CX_METHOD`` / ``CP_METHOD`` / ``AY_METHOD``
"""""""""""""""""""""""""""""""""""""""""""""""

Retrieval method for Total Suspended Matter *C*\ :sub:`X` (Step 2.2),
Chlorophyll-a *C*\ :sub:`P` and CDOM absorption *a*\ :sub:`Y`\ (λ\ :sub:`0`\ ) (Step 2.3).
Each parameter can be derived by any of three pathways, which can be freely combined
(3\ :sup:`3` = 27 versions, see :doc:`methods`).

.. list-table::
   :header-rows: 1
   :widths: 14 28 28 30

   * - Value
     - ``CX_METHOD``
     - ``CP_METHOD``
     - ``AY_METHOD``
   * - ``"A"``
     - Albert (2004), semi-analytical
     - Albert (2004), joint inversion
     - Albert (2004), joint inversion
   * - ``"E1"``
     - Ficek et al. (2011)
     - Ficek et al. (2011)
     - Ficek et al. (2011)
   * - ``"E2"``
     - Parwati et al. (2023)
     - Abbas et al. (2019)
     - Wong et al. (2020)

.. note::
   The currently released ``SDB.py`` / notebook implements ``CX_METHOD`` = ``"E1"``, ``"E2"``,
   ``CP_METHOD`` = ``"A"``, ``"E2"`` and ``AY_METHOD`` = ``"A"``, ``"E1"``. The remaining
   pathways (CX ``"A"``, CP ``"E1"``, AY ``"E2"``) are described in the publication and
   :doc:`methods` but are not yet part of this release; unsupported values raise a
   ``ValueError``.

----

Imports
~~~~~~~

All required Python packages are imported here. The cell also initialises
the project-specific modules ``SDB`` and ``parameters``.

.. code-block:: python

   # --- Standard library ---
   import os, re, glob
   from datetime import datetime

   # --- Numerical & data handling ---
   import numpy as np
   import pandas as pd

   # --- Visualisation ---
   import matplotlib.pyplot as plt
   import matplotlib.colors as mcolors
   from matplotlib.patches import Patch
   import cmocean                          # perceptually uniform oceanographic colourmaps

   # --- Geospatial / raster processing ---
   import rasterio
   from rasterio.enums import Resampling
   from rasterio.warp import reproject
   from rasterio.mask import mask
   from rasterio.features import rasterize
   from shapely.geometry import shape, box, mapping
   from pyproj import Transformer
   import shapely.ops as ops
   import xml.etree.ElementTree as ET     # XML parsing (e.g. Landsat metadata)

   # --- Signal processing & interpolation ---
   from scipy.ndimage import median_filter
   from scipy.interpolate import interp1d
   from scipy.optimize import least_squares

   # --- Machine learning / statistics ---
   from sklearn.linear_model import LinearRegression
   from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

   # --- Google Earth Engine ---
   import ee
   import geemap

   # --- Project modules ---
   import parameters                       # user-defined retrieval parameters
   import SDB as sdb                       # core Cassandra Gemini pipeline functions

   print("✅ All packages loaded")

.. list-table:: Key dependencies
   :header-rows: 1
   :widths: 25 75

   * - Package
     - Purpose
   * - ``numpy``, ``pandas``
     - Numerical computation and tabular data handling
   * - ``rasterio``
     - Reading, writing and reprojecting raster (satellite) data
   * - ``shapely``, ``pyproj``
     - Geometric operations and coordinate reference system transformations
   * - ``scipy``
     - Median filtering, interpolation, and least-squares optimisation
   * - ``sklearn``
     - Sunglint correction (linear regression) and accuracy metrics
   * - ``ee``, ``geemap``
     - Google Earth Engine API access and visualisation
   * - ``cmocean``
     - Perceptually uniform colourmaps for oceanographic variables
   * - ``parameters``
     - Project-specific empirical coefficients and retrieval settings
   * - ``SDB``
     - Core pipeline functions of the *Cassandra Gemini* framework

----


Step 0 – Preprocessing
~~~~~~~~~~~~~~~~~~~~~~~

Loads and preprocesses satellite imagery depending on the selected ``data_source``.
For local files, the cell performs BOA reflectance loading, water masking, and
sunglint correction. In GEE mode, this cell is skipped (handled separately).

.. code-block:: python

   if data_source.lower() == "local":
       aoi = sdb.aoi_from_bbox(152.035771, -23.518535, 152.10007, -23.476975)
       mndwi_threshold = 0.25
       ROOT       = "/path/to/landsat/scene"
       bands_used = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"]
       ref_band   = "SR_B3"
       ...
   else:
       print("📁 GEE mode — skipping local preprocessing.")

**What this cell does:**

1. **Area of Interest:** Defines the spatial extent (AOI) from bounding box coordinates in WGS84.
2. **Scene loading:** Reads all Landsat scenes from the local directory and prepares BOA reflectance arrays.
3. **Metadata enrichment:** Extracts solar and sensor angles from the MTL XML metadata files.
4. **Water masking:** Computes MNDWI per scene and derives a binary water mask using ``mndwi_threshold``.
5. **Value policy:** Sets pixels below ``MIN_VALID_VALUE`` (0.005) or outside the water mask to NaN, depending on the band.
6. **Sunglint correction:** Applies a linear regression between SWIR and visible bands over optically deep water to remove sunglint artefacts .
7. **NaN reapplication:** Ensures that pixels masked before correction remain masked after correction.
8. **Plotting:** Displays MNDWI map, water mask, pre-correction R\ :sub:`rs` per band, and sunglint-corrected R\ :sub:`rs` per band.

.. note::
   Bands SR_B1–SR_B4 receive a minimum-value NaN mask (``below_min``);
   bands SR_B5 and SR_B6 receive a water-only mask (``water_only``),
   since SWIR values outside water are not used in the retrieval.

Step 0b – GEE Authentication & AOI Definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Authenticates with Google Earth Engine and launches an interactive map
for drawing the Area of Interest (AOI). Only executed if
``data_source == "gee"``; skipped in local mode.

.. code-block:: python

   if data_source.lower() == "gee":
       ee.Authenticate()
       ee.Initialize()
       Map = geemap.Map()
       Map.add_draw_control()
       Map.addLayerControl()
       display(Map)
   else:
       print("📁 Local mode — skipping GEE.")

**What this cell does:**

1. **Authentication:** Opens a browser-based OAuth login for Google Earth Engine (required once per session).
2. **Initialisation:** Connects to the GEE backend via ``ee.Initialize()``.
3. **Interactive map:** Displays a ``geemap`` map with drawing tools so the user can define the AOI as a polygon or rectangle directly on the map.

.. note::
   If you prefer to enter coordinates manually, press ENTER without drawing
   and define the AOI in the next cell instead.

----

Step 0c – ROI Capture
^^^^^^^^^^^^^^^^^^^^^

Reads the polygon drawn on the interactive map. If no polygon was drawn,
falls back to manual coordinate input via ``sdb.get_polygon_from_user()``.
Only executed in GEE mode; in local mode the AOI is already defined via
``sdb.aoi_from_bbox()`` in Step 0.

.. code-block:: python

   if data_source.lower() == "gee":
       input("➡️ After drawing ROI press ENTER. ...")
       roi_feature = Map.draw_last_feature
       if roi_feature:
           region = roi_feature.geometry()
       else:
           region = sdb.get_polygon_from_user()
       if region is None:
           raise ValueError("❌ No ROI defined.")
   else:
       pass

**What this cell does:**

1. **Waits for user confirmation** via ``input()`` before reading the map state.
2. **Reads drawn polygon** from the interactive ``geemap`` map (``Map.draw_last_feature``).
3. **Fallback:** If no polygon was drawn, calls ``sdb.get_polygon_from_user()`` for manual coordinate entry.
4. **Validation:** Raises a ``ValueError`` if no ROI could be defined by either method.

----

Step 0d – GEE Image Collection Preview
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Queries the GEE image collection for available scenes within the defined
date range and ROI, and displays them on an interactive preview map.
Only executed in GEE mode.

.. code-block:: python

   collection, Map2 = sdb.gee_preview_new_map(
       mission=mission,
       region=region,
       startdate=startdate,
       enddate=enddate,
       cloudpercentage=None,
       ...
       zoom=10
   )

**What this cell does:**

1. **Guard check:** Raises a ``ValueError`` if the ROI (``region``) has not been defined in the previous cell.
2. **Scene search:** Queries the GEE image catalogue for Landsat scenes intersecting the ROI within ``startdate``–``enddate``.
3. **Optional filtering:** Supports filtering by cloud cover (total, thin cirrus, high, medium), solar zenith angle, and maximum number of layers. All filters are disabled by default (``None``).
4. **Preview map:** Renders an interactive ``geemap`` map (``Map2``) showing all matching scenes for visual inspection before processing.

.. list-table:: Filter parameters
   :header-rows: 1
   :widths: 30 15 55

   * - Parameter
     - Default
     - Description
   * - ``cloudpercentage``
     - ``None``
     - Maximum total cloud cover [%]
   * - ``thincirruspercentage``
     - ``None``
     - Maximum thin cirrus cover [%]
   * - ``highcloudpercentage``
     - ``None``
     - Maximum high cloud cover [%]
   * - ``mediumcloudpercentage``
     - ``None``
     - Maximum medium cloud cover [%]
   * - ``zenith_max``
     - ``None``
     - Maximum solar zenith angle [°]
   * - ``max_layers``
     - ``None``
     - Maximum number of scenes to display
   * - ``zoom``
     - ``10``
     - Initial map zoom level

----

Step 0e – GEE Scene Selection & Preprocessing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Allows the user to select specific scenes from the previewed collection,
then downloads and fully preprocesses the selected imagery via GEE.
Only executed in GEE mode.

.. code-block:: python

   selected_images_list = sdb.select_images_from_collection(collection, region)

   band_images, boa_band_images, extent_bands, bands_used = \
       sdb.process_selected_images_gee(
           mission=mission,
           selected_images_list=selected_images_list,
           region=region,
           target_scale=TARGET_SCALE,
           plot_bands=PLOT_BANDS
       )

**What this cell does:**

1. **Scene selection:** Presents the available scenes from the GEE collection and lets the user select which ones to process.
2. **Download & preprocessing:** Calls ``sdb.process_selected_images_gee()``, which internally performs:

   - DN → BOA reflectance conversion
   - Subsurface remote-sensing reflectance *R*\ :sub:`rs` derivation
   - Water masking and value policy application
   - Sunglint correction
   - Band plotting (if ``PLOT_BANDS == True``)

3. **Outputs:** Returns four objects used throughout the rest of the pipeline:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``band_images``
     - Sunglint-corrected *R*\ :sub:`rs` arrays per scene and band
   * - ``boa_band_images``
     - BOA reflectance arrays per scene and band (pre-correction)
   * - ``extent_bands``
     - Spatial extent of the processed scenes (for plotting)
   * - ``bands_used``
     - List of band names available in the selected scenes

----

Step 0f – Sunglint Correction: Deep Water Reference Area
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Displays the selected scenes on an interactive map so the user can draw
a deep water polygon. This polygon defines the homogeneous, optically deep
reference area used for the sunglint linear regression.
Only executed in GEE mode; in local mode the reference area is defined
via ``sample_polygon`` in Step 0.

.. code-block:: python

   APPLY_SUNGLINT    = True   # enable/disable sunglint correction
   SHOW_SUNGLINT_MAP = True   # enable/disable interactive map display
   SUNGLINT_ZOOM     = 30     # zoom level for the reference area map

   SunglintMap = geemap.Map()
   # add true-colour layers and ROI, then display
   display(SunglintMap)

**What this cell does:**

1. **Control flags:** Sets ``APPLY_SUNGLINT``, ``SHOW_SUNGLINT_MAP``, and ``SUNGLINT_ZOOM`` to control sunglint correction behaviour.
2. **True-colour preview:** Adds all selected scenes as true-colour RGB layers (band combination depends on ``mission``).
3. **ROI overlay:** Draws the Area of Interest boundary in red for spatial orientation.
4. **Deep water drawing:** Enables polygon drawing tools so the user can define a homogeneous, optically deep water area free of shallow signals — this is required as the reference area for the sunglint regression.

.. list-table:: Visualisation parameters
   :header-rows: 1
   :widths: 20 25 55

   * - Mission
     - RGB bands
     - Description
   * - ``"Sentinel"``
     - B4, B3, B2
     - Sentinel-2 true colour (max: 3000)
   * - ``"Landsat"``
     - SR_B4, SR_B3, SR_B2
     - Landsat 8 true colour (max: 25000)

.. note::
   If you prefer to enter coordinates manually, press ENTER without drawing
   and define the deep water polygon in the next cell.

----

Step 0g – Sunglint Reference Polygon Capture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reads the deep water polygon drawn on ``SunglintMap`` and stores it as
``sample_polygon`` for use in the sunglint regression. Falls back to manual
coordinate input if no polygon was drawn. In local mode, the reference
polygon is already defined as the AOI in Step 0 and set to ``None`` here.

.. code-block:: python

   sample_feature = SunglintMap.draw_last_feature
   if sample_feature:
       sample_polygon = sample_feature.geometry()
   else:
       sample_polygon = sdb.get_polygon_from_user()
   if sample_polygon is None:
       raise ValueError("❌ No sunglint sample defined.")

**What this cell does:**

1. **Waits for user confirmation** via ``input()`` before reading the map state.
2. **Reads drawn polygon** from ``SunglintMap`` (``draw_last_feature``).
3. **Fallback:** If no polygon was drawn, calls ``sdb.get_polygon_from_user()`` for manual coordinate entry.
4. **Validation:** Raises a ``ValueError`` if no reference polygon could be defined.
5. **Coordinate printout:** Prints the polygon coordinates for verification.
6. **Local mode:** Sets ``sample_polygon = None``; the reference area is handled internally via the AOI defined in Step 0.

----

Step 0h – Sunglint Correction: Apply to All Scenes (GEE)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Runs the full sunglint correction pipeline across all selected scenes.
For each scene, a linear regression is fitted between the SWIR band and
each visible band over the deep water reference polygon, and the correction
is applied. Only executed in GEE mode.

.. code-block:: python

   all_corrected_images, all_slopes, mndwi_arrays, mndwi_masks = \
       sdb.run_sunglint_for_all_images(
           band_images=band_images,
           boa_band_images=boa_band_images,
           region=region,
           mission=mission,
           bands=bands_used,
           sample_polygon=sample_polygon,
           apply_sunglint=True,
           mndwi_threshold=0.0,
           ...
       )

**What this cell does:**

1. **Water masking:** Computes MNDWI per scene using ``mndwi_threshold = 0.0`` and derives binary water masks.
2. **Sunglint regression:** Fits a linear regression between the SWIR band and each visible band over the deep water reference polygon.
3. **Correction:** Applies the regression to subtract the sunglint contribution from each visible band.
4. **Plotting:** Optionally plots corrected *R*\ :sub:`rs` per band (``plot_corrected_masked``) and MNDWI/water mask grids (``plot_mndwi_grid``).

**Outputs:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Description
   * - ``all_corrected_images``
     - Sunglint-corrected *R*\ :sub:`rs` arrays per scene and band
   * - ``all_slopes``
     - Regression slopes per band per scene (for diagnostics)
   * - ``mndwi_arrays``
     - Raw MNDWI arrays per scene
   * - ``mndwi_masks``
     - Binary water masks per scene

.. list-table:: Key parameters
   :header-rows: 1
   :widths: 30 15 55

   * - Parameter
     - Default
     - Description
   * - ``apply_sunglint``
     - ``True``
     - Set to ``False`` to skip correction and pass images through unchanged
   * - ``mndwi_threshold``
     - ``0.0``
     - MNDWI threshold for water masking during correction
   * - ``set_nonpositive_to_nan``
     - ``False``
     - If ``True``, corrected reflectance values ≤ 0 are set to NaN

----


Step 1 – Empirical Coefficients & Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Mode comparison
   :header-rows: 1
   :widths: 20 40 40

   * -
     - Local mode
     - GEE mode
   * - **Coefficients**
     - Loaded here (both modes)
     - Loaded here (both modes)
   * - **Metadata & angles**
     - Already extracted in Step 0 via ``enrich_metadata_dict_with_angles_local()``
     - Extracted in Step 1.2 via ``extract_metadata_solar_only()``

1.1 Empirical Coefficients (Both Modes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Loads all physics-based model coefficients from ``parameters.py`` and builds
``coef_lookup`` — a per-band dictionary used throughout Steps 2 and 3.

.. code-block:: python

   ars1 = parameters.ars1
   ars2 = parameters.ars2
   prs1 = parameters.prs1  # ... prs2–prs7
   ko  = parameters.ko
   k1u = parameters.k1w
   k2u = parameters.k2w
   k1b = parameters.k1b
   k2b = parameters.k2b

   band_wavelengths, empirical_coefficients = sdb.load_empirical_coefficients(
       parameters, mission
   )
   coef_lookup = sdb.build_coeff_lookup(empirical_coefficients, mission)

.. list-table:: Coefficient groups
   :header-rows: 1
   :widths: 25 75

   * - Variables
     - Description
   * - ``ars1``, ``ars2``
     - Empirical coefficients *A*\ :sub:`rs,1`, *A*\ :sub:`rs,2` of the subsurface reflectance model (Albert 2004)
   * - ``prs1``–``prs7``
     - Empirical coefficients for the deep-water reflectance *R*\ :sub:`rs,∞` (Albert 2004)
   * - ``ko``
     - Empirical coefficient κ\ :sub:`0` in the diffuse attenuation coefficient *K*\ :sub:`d`
   * - ``k1u``, ``k2u``
     - Empirical coefficients for the upwelling attenuation *K*\ :sub:`u,W` (``k1w``, ``k2w`` in ``parameters.py``)
   * - ``k1b``, ``k2b``
     - Empirical coefficients for the bottom attenuation *K*\ :sub:`u,B`

----

1.2 Metadata & Angle Extraction (GEE Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extracts solar geometry from each GEE image and stores it in ``metadata_dict``.
Only executed in GEE mode.

In **local mode**, metadata and angles are already available from Step 0
(``enrich_metadata_dict_with_angles_local()`` reads solar/sensor angles
directly from the Landsat MTL XML files).

.. code-block:: python

   if data_source.lower() == "gee":
       metadata_dict = {}
       for i, img in enumerate(selected_images_list):
           metadata_dict[f"Image_{i+1}"] = sdb.extract_metadata_solar_only(img)

**What this cell does** (GEE only):

Extracts solar zenith and azimuth angles from each selected GEE image.
Stored in ``metadata_dict`` and used in Step 1.3 to compute
*K*\ :sub:`d` and *R*\ :sub:`rs,∞`, and in Step 2 for the radiative
transfer inversion.

----

1.3 Backscattering Albedo, R\ :sub:`rs,∞` and K\ :sub:`d`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Computes three wavelength- and angle-dependent quantities needed as inputs
for the radiative transfer inversion in Step 2. Runs for both GEE and
local mode.

.. code-block:: python

   # Backscattering albedo ω_b
   w = sdb.calc_w(a, bb)

   # Deep water reflectance R_rs,∞
   rrs_inf = sdb.calculate_Rrs_infinity(
       prs1, ..., prs7, theta_v_rad, theta_s_rad, w_value
   )

   # Downward diffuse attenuation coefficient K_d
   kd_val = sdb.calculate_Kd(ko, aW, bW, theta_s_rad)

**What this cell does:**

1. **Backscattering albedo ω\ :sub:`b`:** Computes *w = bbw / (aw + bbw)* per band from pure water absorption (*aw*) and backscattering (*bbw*) coefficients. Bands with missing or invalid coefficients are skipped.

2. **Deep water reflectance R\ :sub:`rs,∞`:** Calculates the reflectance of optically deep water (no bottom contribution) per image and band using the subsurface reflectance model (Albert 2004). Requires solar zenith (*θ*\ :sub:`s`) and sensor viewing angle (*θ*\ :sub:`v`) from the scene metadata.

3. **Diffuse attenuation coefficient K\ :sub:`d`:** Computes how quickly downwelling light is attenuated with depth, as a function of pure water optical properties and solar zenith angle.

**Outputs:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``w_by_band``
     - Backscattering albedo ω\ :sub:`b` per band (dict)
   * - ``results_w_df``
     - Same, as a pandas DataFrame
   * - ``rrs_infinity_df``
     - *R*\ :sub:`rs,∞` per image and band (DataFrame)
   * - ``kd_df``
     - *K*\ :sub:`d` per image and band (DataFrame)

----

Step 2 – Water Constituent Retrieval
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2.1 Water Depth
^^^^^^^^^^^^^^^

Estimates water depth *z*\ :sub:`B` per pixel band-by-band (Step 2.1),
then builds a final depth map from the results (Step 2.1b).
Runs for both GEE and local mode.

.. code-block:: python

   # Step 2.1 – band-wise depth retrieval (plot=False; mosaic below handles plotting)
   depth_results, depth_maps = sdb.compute_depth_maps_albert_slim(
       all_corrected_images=all_corrected_images,
       metadata_dict=metadata_dict,
       bands=bands_used,
       empirical_coefficients=empirical_coefficients,
       parameters=parameters,
       w_by_band=w_by_band,
       kd_results=kd_results,
       rrs_infinity_results=rrs_infinity_results,
       calculate_depth_Albert=sdb.calculate_depth_Albert,
       extent=extent_bands,
       plot=False,
       set_nonpositive_to_zero=True,
   )

   # Step 2.1b – build final depth map (SR_B4 only)
   mosaic, info = sdb.build_depth_mosaic(
       mission=mission,
       depth_results=depth_results,
       bands=bands_used,
       image_idx=0,
       extent=extent_bands,
       USE_SINGLE_BAND=True,
       SINGLE_BAND_NAME="SR_B4",
       PLOT_MOSAIC=True
   )

**What this cell does:**

1. **Band-wise depth retrieval:** Inverts the radiative transfer model per pixel and band using *K*\ :sub:`d`, *R*\ :sub:`rs,∞`, and *ω*\ :sub:`b` from Step 1.3. Band-level plots skipped (``plot=False``).
2. **Depth mosaic:** Builds the final depth map. Currently SR_B4 only (``USE_SINGLE_BAND=True``).

.. list-table:: Available mosaic strategies
   :header-rows: 1
   :widths: 25 75

   * - Strategy
     - Description
   * - **Single band** *(current)*
     - Uses only one band. Set ``USE_SINGLE_BAND=True``, ``SINGLE_BAND_NAME="SR_B4"``.
   * - Hard-cut mosaic
     - SR_B4 up to ``SWITCH_DEPTH_LANDSAT`` (default 5 m), then SR_B3. Set ``USE_HARD_CUT=True`` (default in ``SDB.py``).
   * - Smooth blend
     - Blends SR_B4→SR_B3 across ``[BLEND_START, BLEND_END]``. Set ``USE_SMOOTH_BLEND=True``.

.. list-table:: Outputs
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``depth_results``
     - Per-pixel depth estimates per scene and band
   * - ``depth_maps``
     - 2D depth arrays per scene and band; used as initial values in Step 3
   * - ``mosaic``
     - Final 2D float32 depth map
   * - ``info``
     - Diagnostics dict (strategy, calibration status, pixel counts)

----

2.2 Total Suspended Matter
^^^^^^^^^^^^^^^^^^^^^^^^^^

Computes the TSM concentration *C*\ :sub:`X` per pixel for all scenes, using the
pathway selected via ``CX_METHOD`` (``"A"``, ``"E1"`` or ``"E2"``, see above and :doc:`methods`).
Runs for both GEE and local mode.

.. code-block:: python

   if CX_METHOD == "E2":
       # Parwati et al. (2023)
       Cx_results = sdb.compute_cx_tss_for_all_images(
           mission=mission, all_corrected_images=all_corrected_images,
           region=region, plot=True, plot_contours=True,
       )
   elif CX_METHOD == "E1":
       # Ficek et al. (2011): C_X = 5590 * R_rs(798)^0.95
       Cx_results = sdb.compute_cx_cspm_for_all_images(
           mission=mission, all_corrected_images=all_corrected_images,
           region=region, plot=True, plot_contours=True,
       )
   else:
       raise ValueError(f"Unknown CX_METHOD: {CX_METHOD}")

   # Post-processing: replace NaN with 0
   for entry in Cx_results:
       arr = entry["C_X"]
       arr[np.isnan(arr)] = 0
       entry["C_X"] = arr

Retrieves *C*\ :sub:`X` [g m\ :sup:`-3`] and replaces NaN pixels by 0. The result serves as
initial estimate in Step 3.1 (and as input to Step 2.3 Method A).

.. list-table:: Outputs
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``Cx_results``
     - List of dicts with keys ``"Image"`` and ``"C_X"`` (2D float32 [g m\ :sup:`-3`]) per scene

----

2.3 Phytoplankton Chlorophyll-a and CDOM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*C*\ :sub:`P` and *a*\ :sub:`Y` are retrieved either jointly with the Albert (2004)
inversion (``"A"``, Step 2.3c) or individually with the empirical methods ``"E1"``/``"E2"``.
If ``"A"`` is chosen for either parameter, Step 2.3c is executed and overwrites the results
of Steps 2.3a and 2.3b.

2.3a – Chlorophyll-a (``CP_METHOD == "E2"``)
"""""""""""""""""""""""""""""""""""""""""""""

.. code-block:: python

   Chl_results = []

   if CP_METHOD == "E2":
       # Abbas et al. (2019): GROC-4 algorithm
       CP_results = sdb.compute_cp_abbas_groc4_for_all_images(
           mission=mission, all_corrected_images=all_corrected_images,
           region=region, plot=True, verbose=True,
       )
       for entry in CP_results:
           arr = entry["C_P"]
           arr[np.isnan(arr)] = 0
           entry["C_P"] = arr
           Chl_results.append({"Image": entry["Image"], "C_a": entry["C_P"]})

Retrieves *C*\ :sub:`a` [µg L\ :sup:`-1`]; NaN pixels are set to 0 and the result is stored
under the key ``"C_a"``.

2.3b – CDOM absorption (``AY_METHOD == "E1"``)
""""""""""""""""""""""""""""""""""""""""""""""""

.. code-block:: python

   a_CDOM_results_alt = []

   if AY_METHOD == "E1":
       # Ficek et al. (2011)
       aY_results = sdb.compute_cdom_for_all_images(
           mission=mission, all_corrected_images=all_corrected_images,
           region=region, plot=True, landsat_min_clip=0.1,
       )
       for entry in aY_results:
           arr = entry["a_CDOM"]
           arr[np.isnan(arr)] = 0
           entry["a_CDOM"] = arr
           a_CDOM_results_alt.append({"Image": entry["Image"], "a_CDOM": arr})

Retrieves *a*\ :sub:`Y`\ (λ₀) [m\ :sup:`-1`]; NaN values are replaced by 0.

2.3c – Albert Joint Inversion (*C*\ :sub:`P` + *a*\ :sub:`Y`)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Run this cell when ``AY_METHOD == "A"`` **or** ``CP_METHOD == "A"``.
Simultaneously retrieves *C*\ :sub:`P` (Chl-a) and *a*\ :sub:`Y`\ (λ₀) (CDOM)
via pixel-wise optimisation of the full radiative transfer model (Albert 2004).
**Overwrites** ``Chl_results`` (from Step 2.3) and ``a_CDOM_results_alt`` (from Step 2.3b).

.. code-block:: python

   # STEP 2.3c – ALBERT JOINT INVERSION: C_P (Chl-a) + a_Y(λ₀) (CDOM)
   # Run when AY_METHOD == "A" OR CP_METHOD == "A".
   # Overwrites Chl_results and a_CDOM_results_alt.
   if AY_METHOD == "A" or CP_METHOD == "A":
       Chl_results = []
       a_CDOM_results_alt = []

       # Step 1: pixel-wise inversion of total absorption a(λ) via RTM optimisation
       a_results = sdb.compute_a_maps_albert(
           mission=mission,
           all_corrected_images=all_corrected_images,
           Cx_results=Cx_results,
           depth_mosaic_results=depth_mosaic_results,
           metadata_dict=metadata_dict,
           empirical_coefficients=empirical_coefficients,
           rrs_infinity_results=rrs_infinity_results,
           ars1=ars1, ars2=ars2,        # spectral shape coefficients
           ko=ko, k1u=k1u, k2u=k2u,    # upwelling path length factors
           k1b=k1b, k2b=k2b,           # backscattering path length factors
           region=region,
           optimize_a_pixelwise_fn=sdb.optimize_a_pixelwise_fast,
           plot=False,
       )

       # Step 2: decompose a(λ) into C_P (Chl-a) and a_Y(λ₀) (CDOM)
       # using two-band approach from Albert (2004)
       cp_ay_results = sdb.compute_cp_ay_albert_from_a_two_bands(
           mission=mission,
           a_results=a_results,
           empirical_coefficients=empirical_coefficients,
           region=region,
           plot=False,
       )

       # Replace NaN with 0 for both products
       for entry in cp_ay_results:
           arr = entry["a_Y_lambda0"]
           arr[np.isnan(arr)] = 0
           entry["a_Y_lambda0"] = arr

           arr = entry["C_P"]
           arr[np.isnan(arr)] = 0
           entry["C_P"] = arr

       # Store in unified output format
       for entry in cp_ay_results:
           Chl_results.append({
               "Image": entry["Image"],
               "C_a": entry["C_P"]              # Chl-a [µg/L]
           })
           a_CDOM_results_alt.append({
               "Image": entry["Image"],
               "a_CDOM": entry["a_Y_lambda0"]   # CDOM absorption [m⁻¹]
           })

       print("✅ Chl_results:", len(Chl_results))
       print("✅ a_CDOM_results_alt:", len(a_CDOM_results_alt))

       # Quick overview plot: C_P and a_Y side by side for first scene
       sdb.quick_plot_cp_ay(image_idx=1, cp_ay_results=cp_ay_results, region=region)

**What this cell does:**

Inverts the radiative transfer model pixel-wise to retrieve the total absorption
coefficient *a*(λ), then decomposes it into *C*\ :sub:`P` and *a*\ :sub:`Y`\ (λ₀)
using a two-band approach. This is the most physically consistent method but also
the most computationally expensive.

.. list-table:: Outputs
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``Chl_results``
     - List of dicts with keys ``"Image"`` and ``"C_a"`` (2D float32 [µg L\ :sup:`-1`]) per scene
   * - ``a_CDOM_results_alt``
     - List of dicts with keys ``"Image"`` and ``"a_CDOM"`` (2D float32 [m\ :sup:`-1`]) per scene

----


Step 3 – Parameter Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3.1 Parameter Optimisation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Core optimisation loop. For each image and each band, jointly optimises
water depth *z*\ :sub:`B`, TSM *C*\ :sub:`X`, Chl-a *C*\ :sub:`P`,
CDOM *a*\ :sub:`Y`, and bottom reflectance *R*\ :sub:`b` per pixel by
minimising the residual between measured *R*\ :sub:`rs` and the RTM
forward model. Uses the outputs of Steps 2.1–2.3 as initial estimates.

.. code-block:: python

   # Bottom reflectance optimisation bounds per band
   band_specific_rb_bounds = {
       "SR_B1": (0, 0.7),
       "SR_B2": (0, 0.7),
       "SR_B3": (0, 0.7),
       "SR_B4": (0, 0.7),
       "SR_B5": (0, 0.7),
       "SR_B6": (0, 0.7),
   }

   # Output containers: {image_idx: {band: 2D array}}
   zB_all_bands = {}   # optimised depth [m]
   CX_all_bands = {}   # optimised TSM [g/m³]
   CP_all_bands = {}   # optimised Chl-a [µg/L]
   aY_all_bands = {}   # optimised CDOM [m⁻¹]
   Rb_all_bands = {}   # optimised bottom reflectance [-]

   num_images = len(all_corrected_images)
   extent = sdb._extent_from_region(region)

   for i0 in range(num_images):
       image_idx = i0 + 1  # 1-based (consistent with other result dicts)
       metadata = metadata_dict.get(f"Image_{image_idx}", None)
       if metadata is None:
           continue

       # Initial estimates from previous pipeline steps
       zB_init = next((d["Mosaic_Depth"] for d in depth_mosaic_results if d.get("Image") == image_idx), None)
       CX_init = next((d["C_X"]         for d in Cx_results             if d.get("Image") == image_idx), None)
       CP_init = next((d["C_a"]         for d in Chl_results            if d.get("Image") == image_idx), None)
       aY_init = next((d["a_CDOM"]      for d in a_CDOM_results_alt     if d.get("Image") == image_idx), None)

       for band in bands_used:
           if band not in all_corrected_images[i0]:
               continue

           R_rs = np.squeeze(all_corrected_images[i0][band])

           result = sdb.optimize_one_band(
               mission=mission,
               image_idx_1based=image_idx,
               band=band,
               R_rs_measured=R_rs,
               zB_init=zB_init,
               CX_init=CX_init,
               CP_init=CP_init,
               aY_init=aY_init,
               empirical_coefficients=empirical_coefficients,
               band_wavelengths=band_wavelengths,
               rb_bounds=band_specific_rb_bounds,
               metadata=metadata,
               rrs_infinity_results=rrs_infinity_results,
               ars1=ars1, ars2=ars2,
               ko=ko, k1u=k1u, k2u=k2u, k1b=k1b, k2b=k2b,
               extent=extent,
               plot=True,
           )

           if result is None:
               continue

           zB_all_bands.setdefault(image_idx, {})[band] = result["zB"]
           CX_all_bands.setdefault(image_idx, {})[band] = result["CX"]
           CP_all_bands.setdefault(image_idx, {})[band] = result["CP"]
           aY_all_bands.setdefault(image_idx, {})[band] = result["aY"]
           Rb_all_bands.setdefault(image_idx, {})[band] = result["RB"]

**What this cell does:**

Iterates over all images and bands. For each combination, ``optimize_one_band()``
runs a pixel-wise non-linear optimisation of the Albert RTM, using the
outputs of Steps 2.1–2.3 as starting points. Results are stored in nested dicts
``{image_idx: {band: 2D array}}``.

.. note::
   ``band_specific_rb_bounds`` defines the valid range for *R*\ :sub:`b` per
   band. If tighter per-band bounds are needed (e.g. SR_B1 ≤ 0.35), update the
   dict before running — duplicate keys are silently overwritten by Python, so
   the last definition wins.

.. list-table:: Outputs
   :header-rows: 1
   :widths: 20 80

   * - Variable
     - Description
   * - ``zB_all_bands``
     - Optimised water depth *z*\ :sub:`B` [m] per image and band
   * - ``CX_all_bands``
     - Optimised TSM *C*\ :sub:`X` [g m\ :sup:`-3`] per image and band
   * - ``CP_all_bands``
     - Optimised Chl-a *C*\ :sub:`P` [µg L\ :sup:`-1`] per image and band
   * - ``aY_all_bands``
     - Optimised CDOM *a*\ :sub:`Y` [m\ :sup:`-1`] per image and band
   * - ``Rb_all_bands``
     - Optimised bottom reflectance *R*\ :sub:`b` [-] per image and band

----

3.2 Results: Depth Map Export
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Selects the final water depth map *z*\ :sub:`B` (SR_B4, case ``B4`` / pipeline mode ``A``),
saves it as GeoTIFF and displays it using the ``cmo.deep`` colourmap.

.. code-block:: python

   OUTPUT_ROOT = "/path/to/output"

   for image_idx in range(1, len(all_corrected_images) + 1):
       sdb.run_case_for_image(
           mission=mission,
           image_idx=image_idx,
           extent_plot=extent,
           scene_id="1",
           output_root=OUTPUT_ROOT,
           zB_all_bands=zB_all_bands,
       )

**Output:** ``<OUTPUT_ROOT>/<scene_id>/Image_<NN>/CASE_B4_A/zB.tif`` — single-band float32
GeoTIFF (EPSG:4326), water depth in metres, NaN = no data.

----

Water Level Correction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Water level correction is **not part of the notebook pipeline** — it is applied
externally to the final depth outputs from Step 3.2 before further use or
validation. The appropriate method depends on the water body type.

.. list-table:: Correction approaches by water body type
   :header-rows: 1
   :widths: 20 30 50

   * - Water body
     - Method
     - Notes
   * - **Ocean / tidal coast**
     - Tidal model (e.g. FES2022, TPXO)
     - Global or regional tidal constituents; applied at the scene acquisition timestamp
   * - **Ocean / tidal coast**
     - Gauge measurements
     - Preferred if a nearby tide gauge is available; higher local accuracy
   * - **Lake / reservoir**
     - Gauge measurements
     - Water level from limnological gauge or remote sensing (e.g. satellite altimetry)
   * - **Estuary / lagoon**
     - Tidal model + gauge
     - Combined approach recommended; tidal signal plus fluvial influence

.. note::
   The corrected depth *z*\ :sub:`B,corr` is obtained by subtracting the water
   level anomaly Δ\ *h* (relative to the chart datum used for reference depth)
   from the retrieved *z*\ :sub:`B`:

   *z*\ :sub:`B,corr` = *z*\ :sub:`B` − Δ\ *h*

----

sdb.py
------

``sdb.py`` is the core module of the Cassandra Gemini framework. It contains
the implementations of all formulas and algorithms applied throughout the
pipeline — from preprocessing and radiative transfer inversion to parameter
optimisation and output export. All functions used in ``CassandraGemini.ipynb`` are
imported from this module at the start of the notebook.

.. note::
   Detailed API documentation for ``sdb.py`` is not published at this time.

----

parameters.py
-------------

``parameters.py`` provides the sensor-specific empirical coefficients and
spectral properties required by the retrieval algorithms. The current
implementation is calibrated for **Landsat 8 OLI**, including band-specific
wavelengths, radiometric characteristics, and the empirical constants used
in the Albert (2004) radiative transfer model.

.. note::
   Detailed documentation for ``parameters.py`` is not published at this time.