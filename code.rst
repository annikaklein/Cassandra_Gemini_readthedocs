Code Application
================

SDB.ipynb
---------

Configuration
~~~~~~~~~~~~~

Before running the pipeline, all user-defined parameters must be set
in the configuration cell. The pipeline follows the processing structure
shown in Figure x, proceeding from preprocessing through water depth
estimation, water constituent retrieval, parameter optimization, and
tide correction.

Quick Start
^^^^^^^^^^^

.. code-block:: python

   mission      = "Landsat"
   data_source  = "gee"
   startdate    = "2014-03-15"
   enddate      = "2014-04-30"
   TARGET_SCALE = 10
   PLOT_BANDS   = True
   CX_METHOD    = "albert"
   CP_METHOD    = "ficek"
   AY_METHOD    = "wong"

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

.. note::
   Scenes are filtered to minimize temporal distance to in-situ reference
   measurements. See Section 5.1 for details on scene selection criteria.

----

``TARGET_SCALE``
""""""""""""""""

Target pixel size in metres. Images are resampled to this resolution
via bilinear interpolation.

**Default:** ``10``

----

``PLOT_BANDS``
""""""""""""""

If ``True``, intermediate processing steps and band results are
displayed as plots.

**Default:** ``True``

----

``CX_METHOD``
"""""""""""""

Method used to estimate Total Suspended Matter concentration *C*\ :sub:`X`
(Step 2.2 in the pipeline).

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Value
     - Reference
   * - ``"albert"``
     - Albert (2004)
   * - ``"ficek"``
     - Ficek et al. (2011)
   * - ``"parwarti"``
     - Parwati et al. (2022)

----

``CP_METHOD``
"""""""""""""

Method used to estimate Phytoplankton Chlorophyll-a concentration *C*\ :sub:`P`
(Step 2.3 in the pipeline).

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Value
     - Reference
   * - ``"albert"``
     - Albert (2004)
   * - ``"ficek"``
     - Ficek et al. (2011)
   * - ``"abbas"``
     - Abbas et al. (2019)

----

``AY_METHOD``
"""""""""""""

Method used to estimate CDOM absorption *a*\ :sub:`Y`\ (λ\ :sub:`0`\ )
(Step 2.3 in the pipeline).

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Value
     - Reference
   * - ``"albert"``
     - Albert (2004)
   * - ``"ficek"``
     - Ficek et al. (2011)
   * - ``"wong"``
     - Wong et al. (2019)

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
6. **Sunglint correction:** Applies a linear regression between SWIR and visible bands over optically deep water to remove sunglint artefacts (see Eq. 4).
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
reference area used for the sunglint linear regression (Eq. 4).
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
is applied following Eq. 4. Only executed in GEE mode.

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
           mndwi_threshold=0.75,
           ...
       )

**What this cell does:**

1. **Water masking:** Computes MNDWI per scene using ``mndwi_threshold = 0.75`` and derives binary water masks.
2. **Sunglint regression:** Fits a linear regression between the SWIR band and each visible band over the deep water reference polygon.
3. **Correction:** Applies the regression to subtract the sunglint contribution from each visible band (Eq. 4).
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
     - ``0.75``
     - MNDWI threshold for water masking during correction
   * - ``set_nonpositive_to_nan``
     - ``False``
     - If ``True``, corrected reflectance values ≤ 0 are set to NaN

----


Step 1 – Empirical Coefficients & Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.1 Empirical Coefficients & Backscattering Albedo ω\ :sub:`b`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Loads physics-based empirical coefficients from ``parameters.py`` and
extracts scene metadata (solar angles) from the selected images.
Only the GEE branch is shown here; in local mode both are handled in Step 0.

.. code-block:: python

   # Coefficients
   band_wavelengths, empirical_coefficients = sdb.load_empirical_coefficients(
       parameters, mission
   )
   coef_lookup = sdb.build_coeff_lookup(empirical_coefficients, mission)

   # Metadata
   metadata_dict = {}
   for i, img in enumerate(selected_images_list):
       metadata_dict[f"Image_{i+1}"] = sdb.extract_metadata_solar_only(img)

**What this cell does:**

1. **Empirical coefficients:** Loads all physics-based model coefficients from ``parameters.py``, including backscattering albedo coefficients (*ars1*, *ars2*), subsurface reflectance model coefficients (*prs1–prs7*), and attenuation/backscattering coefficients (*ko*, *k1u*, *k2u*, *k1b*, *k2b*).
2. **Coefficient lookup:** Builds a per-band dictionary (``coef_lookup``) for fast access during the retrieval steps.
3. **Metadata extraction:** Extracts solar geometry (sun elevation, azimuth) from each GEE image via ``sdb.extract_metadata_solar_only()``. Required for angle conversion and attenuation correction.

.. list-table:: Coefficient groups
   :header-rows: 1
   :widths: 25 75

   * - Variables
     - Description
   * - ``ars1``, ``ars2``
     - Backscattering albedo coefficients (Albert & Mobley 2003)
   * - ``prs1``–``prs7``
     - Subsurface reflectance model coefficients
   * - ``ko``
     - Pure water absorption coefficient
   * - ``k1u``, ``k2u``
     - Upwelling diffuse attenuation coefficients
   * - ``k1b``, ``k2b``
     - Bottom attenuation coefficients

----
1.1 Empirical Coefficients (Both Modes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Loads all physics-based model coefficients from ``parameters.py``.
This cell runs for both GEE and local mode.

.. code-block:: python

   # Backscattering albedo
   ars1 = parameters.ars1
   ars2 = parameters.ars2

   # Subsurface reflectance model
   prs1 = parameters.prs1
   # ... prs2–prs7

   # Attenuation coefficients
   ko  = parameters.ko
   k1u = parameters.k1w
   k2u = parameters.k2w
   k1b = parameters.k1b
   k2b = parameters.k2b

   band_wavelengths, empirical_coefficients = sdb.load_empirical_coefficients(
       parameters, mission
   )
   coef_lookup = sdb.build_coeff_lookup(empirical_coefficients, mission)

**What this cell does:**

Reads all empirical constants from ``parameters.py`` into the notebook namespace
and builds ``coef_lookup`` — a per-band dictionary used throughout Steps 2 and 3
for fast coefficient access during the radiative transfer inversion.

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
     - Extracted here via ``extract_metadata_solar_only()``

----

1.1 Empirical Coefficients (Both Modes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Loads all physics-based model coefficients from ``parameters.py``.
Runs for both GEE and local mode.

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

**What this cell does:**

Reads all empirical constants from ``parameters.py`` into the notebook namespace
and builds ``coef_lookup`` — a per-band dictionary used throughout Steps 2 and 3
for fast coefficient access during the radiative transfer inversion.

.. list-table:: Coefficient groups
   :header-rows: 1
   :widths: 25 75

   * - Variables
     - Description
   * - ``ars1``, ``ars2``
     - Backscattering albedo coefficients (Albert & Mobley 2003)
   * - ``prs1``–``prs7``
     - Subsurface reflectance model coefficients
   * - ``ko``
     - Pure water absorption coefficient
   * - ``k1u``, ``k2u``
     - Upwelling diffuse attenuation coefficients
   * - ``k1b``, ``k2b``
     - Bottom attenuation coefficients

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

2. **Deep water reflectance R\ :sub:`rs,∞`:** Calculates the reflectance of optically deep water (no bottom contribution) per image and band using the subsurface reflectance model (Albert & Mobley 2003). Requires solar zenith (*θ*\ :sub:`s`) and sensor viewing angle (*θ*\ :sub:`v`) from the scene metadata.

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
       PLOT_MOSAIC=True,
       TITLE_PREFIX="Input Mosaic Depth | SR_B4 only"
   )

**What this cell does:**

1. **Band-wise depth retrieval:** Inverts the radiative transfer model (Eq. 8) per pixel and band using *K*\ :sub:`d`, *R*\ :sub:`rs,∞`, and *ω*\ :sub:`b` from Step 1.3. Band-level plots skipped (``plot=False``).
2. **Depth mosaic:** Builds the final depth map. Currently SR_B4 only (``USE_SINGLE_BAND=True``).

.. list-table:: Available mosaic strategies
   :header-rows: 1
   :widths: 25 75

   * - Strategy
     - Description
   * - **Single band** *(current)*
     - Uses only one band. Set ``USE_SINGLE_BAND=True``, ``SINGLE_BAND_NAME="SR_B4"``.
   * - Hard-cut mosaic
     - SR_B4 up to ``SWITCH_DEPTH``, then SR_B3. Set ``USE_HARD_CUT=True``.
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

Computes the Total Suspended Matter (TSM) concentration *C*\ :sub:`X`
per pixel for all scenes. Three methods are supported, selected via
``CX_METHOD`` in the configuration cell. Runs for both GEE and local mode.

.. code-block:: python

   # --- SELECT METHOD AND COMPUTE C_X ---
   if CX_METHOD == "albert":
       # Albert & Mobley (2003): physics-based retrieval using reflectance
       # above water (R_u), spectral shape functions (f_arrow), and
       # empirical coefficients. Requires depth, K_d, R_rs∞, and ω_b.
       Cx_results = []
       Cx_results = sdb.compute_cx_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           depth_mosaic_results=depth_mosaic_results,
           metadata_dict=metadata_dict,
           empirical_coefficients=empirical_coefficients,
           kd_df=kd_df,
           region=region,
           results_w=results_w,
           rrs_infinity_results=rrs_infinity_results,
           calculate_f_arrow=sdb.calculate_f_arrow,
           calculate_f_arrow_land=sdb.calculate_f_arrow_land,
           calculate_R_u=sdb.calculate_R_u,
           calculate_Cx=sdb.calculate_Cx,
           ars1=ars1,
           ars2=ars2,
           plot_ru=True,       # plot above-water reflectance R_u
           plot_cx=True,       # plot C_X concentration map
           plot_contours=True, # overlay depth contours on C_X plot
       )
   elif CX_METHOD == "parwarti":
       # Parwati et al. (2022): empirical band-ratio method (no depth needed)
       Cx_results = []
       Cx_results = sdb.compute_cx_tss_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           region=region,
           plot=True,
           plot_contours=True,
       )
   elif CX_METHOD == "ficek":
       # Ficek et al. (2011): empirical formula calibrated for Baltic Sea waters
       Cx_results = []
       Cx_results = sdb.compute_cx_cspm_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           region=region,
           plot=True,
           plot_contours=True,
       )
   else:
       raise ValueError(f"Unknown CX_METHOD: {CX_METHOD}")

   # --- POST-PROCESSING ---
   # Replace NaN with 0 and cap at 200 g/m³ to remove outliers / land artefacts
   for entry in Cx_results:
       arr = entry["C_X"]
       arr[np.isnan(arr)] = 0
       arr[arr >= 200] = 200
       entry["C_X"] = arr

   print("✅ Cx_results:", len(Cx_results))

   # Store result as list of dicts (consistent format with depth_mosaic_results)
   Cx_results.append({"Image": 1, "C_X": Cx_results})

**What this cell does:**

Retrieves the TSM concentration *C*\ :sub:`X` [g m\ :sup:`-3`] per pixel
using the method specified by ``CX_METHOD``. After retrieval, NaN pixels are
set to 0 and values ≥ 200 g m\ :sup:`-3` are capped to suppress land
artefacts and extreme outliers.

.. list-table:: Method comparison
   :header-rows: 1
   :widths: 20 20 60

   * - ``CX_METHOD``
     - Reference
     - Description
   * - ``"albert"``
     - Albert & Mobley (2003)
     - Physics-based; uses *R*\ :sub:`u`, spectral shape functions, *K*\ :sub:`d`, *R*\ :sub:`rs,∞`, *ω*\ :sub:`b`. Most inputs required.
   * - ``"parwarti"``
     - Parwati et al. (2022)
     - Empirical band-ratio method. No depth or optical parameters needed.
   * - ``"ficek"``
     - Ficek et al. (2011)
     - Empirical formula; calibrated for Baltic Sea waters.

.. list-table:: Outputs
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``Cx_results``
     - List of dicts with key ``"C_X"`` (2D float32 array [g m\ :sup:`-3`]) per scene

----

2.3 Phytoplankton Chlorophyll-a and CDOM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Computes the phytoplankton Chlorophyll-a concentration *C*\ :sub:`a`
per pixel for all scenes. The method is selected via ``CP_METHOD`` in
the configuration cell. Runs for both GEE and local mode.

.. code-block:: python

   # --- SELECT METHOD AND COMPUTE C_P (Chlorophyll-a) ---
   Chl_results = []

   if CP_METHOD == "ficek":
       # Ficek et al. (2011): empirical formula calibrated for Baltic Sea waters
       CP_results = sdb.compute_cp_ficek_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           region=region,
           plot=True,
           verbose=True,
       )
   elif CP_METHOD == "abbas":
       # Abbas et al. (2019): GROC-4 algorithm for phytoplankton Chl-a retrieval
       CP_results = sdb.compute_cp_abbas_groc4_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           region=region,
           plot=True,
           verbose=True,
       )
   else:
       raise ValueError(CP_METHOD)

   # --- POST-PROCESSING ---
   # Replace NaN with 0 (no upper cap needed for Chl-a)
   for entry in CP_results:
       arr = entry["C_P"]
       arr[np.isnan(arr)] = 0
       entry["C_P"] = arr

   # Rename C_P → C_a (chlorophyll-a) for consistent downstream naming
   for entry in CP_results:
       Chl_results.append({
           "Image": entry["Image"],
           "C_a": entry["C_P"]
       })

   print("✅ Chl_results:", len(Chl_results))

**What this cell does:**

Retrieves Chlorophyll-a concentration *C*\ :sub:`a` [µg L\ :sup:`-1`]
per pixel using the method specified by ``CP_METHOD``. NaN pixels are
set to 0. The result is stored under the key ``"C_a"`` for consistent
naming in downstream steps.

.. list-table:: Method comparison (``CP_METHOD``)
   :header-rows: 1
   :widths: 20 20 60

   * - Value
     - Reference
     - Description
   * - ``"ficek"``
     - Ficek et al. (2011)
     - Empirical formula; calibrated for Baltic Sea waters.
   * - ``"abbas"``
     - Abbas et al. (2019)
     - GROC-4 algorithm for phytoplankton Chl-a retrieval.

----

2.3b – CDOM Absorption Coefficient *a*\ :sub:`Y`\ (λ₀)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Computes *a*\ :sub:`Y`\ (λ₀) [m\ :sup:`-1`] per pixel using an empirical or
semi-analytical method (``ficek`` or ``wong``). Run this cell when
``AY_METHOD`` is **not** ``"albert"``; for the Albert case, use Step 2.3c instead.

.. code-block:: python

   # STEP 2.3b – CDOM ABSORPTION COEFFICIENT a_Y(λ₀)
   # Run when AY_METHOD is "ficek" or "wong".
   a_CDOM_results_alt = []

   if AY_METHOD == "ficek":
       # Ficek et al. (2011): empirical model calibrated for Baltic Sea waters
       aY_results = sdb.compute_cdom_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           region=region,
           plot=True,
           landsat_min_clip=0.1,  # clip low reflectances before inversion
       )
   elif AY_METHOD == "wong":
       # Wong et al. (2019): semi-analytical a_Y retrieval
       aY_results = sdb.compute_ay_wong_for_all_images(
           mission=mission,
           all_corrected_images=all_corrected_images,
           region=region,
           plot=True,
           plot_contours=True,
           clip_aY=(0.0, 5.0),  # constrain to physically plausible range [m⁻¹]
       )
   else:
       raise ValueError(f"Unknown AY_METHOD: {AY_METHOD}")

   # Replace NaN with 0
   for entry in aY_results:
       arr = entry["a_CDOM"]
       arr[np.isnan(arr)] = 0
       entry["a_CDOM"] = arr

   # Store in unified output format
   for entry in aY_results:
       a_CDOM_results_alt.append({
           "Image": entry["Image"],
           "a_CDOM": entry["a_CDOM"]
       })

   print("✅ a_CDOM_results:", len(a_CDOM_results_alt))

**What this cell does:**

Retrieves the CDOM absorption coefficient *a*\ :sub:`Y`\ (λ₀) per pixel using
the method set by ``AY_METHOD``. NaN values are replaced with 0.

.. list-table:: Method comparison (``AY_METHOD``)
   :header-rows: 1
   :widths: 20 20 60

   * - Value
     - Reference
     - Description
   * - ``"ficek"``
     - Ficek et al. (2011)
     - Empirical model; calibrated for Baltic Sea waters.
   * - ``"wong"``
     - Wong et al. (2019)
     - Semi-analytical retrieval; clipped to [0, 5] m\ :sup:`-1`.

.. list-table:: Outputs
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Description
   * - ``a_CDOM_results_alt``
     - List of dicts with keys ``"Image"`` and ``"a_CDOM"`` (2D float32 [m\ :sup:`-1`]) per scene

----

2.3c – Albert Joint Inversion (*C*\ :sub:`P` + *a*\ :sub:`Y`)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Run this cell when ``AY_METHOD == "albert"`` **or** ``CP_METHOD == "albert"``.
Simultaneously retrieves *C*\ :sub:`P` (Chl-a) and *a*\ :sub:`Y`\ (λ₀) (CDOM)
via pixel-wise optimisation of the full radiative transfer model (Albert & Mobley 2003).
**Overwrites** ``Chl_results`` (from Step 2.3) and ``a_CDOM_results_alt`` (from Step 2.3b).

.. code-block:: python

   # STEP 2.3c – ALBERT JOINT INVERSION: C_P (Chl-a) + a_Y(λ₀) (CDOM)
   # Run when AY_METHOD == "albert" OR CP_METHOD == "albert".
   # Overwrites Chl_results and a_CDOM_results_alt.
   if AY_METHOD == "albert" or CP_METHOD == "albert":
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
       # using two-band approach from Albert & Mobley (2003)
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

Not mandatory - Load & Align Reference Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Loads in-situ reference measurements (depth, *C*\ :sub:`X`, *C*\ :sub:`P`,
*a*\ :sub:`Y`) stored as GeoTIFFs and aligns them to the satellite image grid
before parameter optimisation. Reprojects and resamples each file to
``target_shape`` and ``extent_target`` via bilinear interpolation.

.. code-block:: python

   # STEP 3.0 – LOAD & ALIGN REFERENCE DATA (in-situ GeoTIFFs)
   image_idx = 0  # index of the scene to use for optimisation

   # Determine spatial extent — use extent_bands if available
   if "extent_bands" in globals() and extent_bands is not None:
       extent_target = extent_bands
   elif "extent" in globals() and extent is not None:
       extent_target = extent
   else:
       # Derive bounding box from GEE region geometry
       coords = region.bounds().coordinates().getInfo()[0]
       lon_min, lat_min = coords[0]
       lon_max, lat_max = coords[2]
       extent_target = [lon_min, lon_max, lat_min, lat_max]

   # Reference band for pixel grid shape (B7: Sentinel, SR_B3: Landsat)
   if mission == "Sentinel":
       target_arr = np.squeeze(all_corrected_images[image_idx]["B7"])
   else:
       target_arr = np.squeeze(all_corrected_images[image_idx]["SR_B3"])
   target_shape = target_arr.shape

   print("✅ extent_target:", extent_target)
   print("✅ target_shape:", target_shape)

   # Reference GeoTIFFs (in-situ / validation dataset)
   reference_paths = {
       "depth": "/Users/.../Input/depth.tif",
       "cx":    "/Users/.../Input/CXE1.tif",
       "cp":    "/Users/.../Input/CPE1.tif",
       "ay":    "/Users/.../Input/AYA.tif",
   }

   # Load and align each reference file to the satellite image grid
   reference_data = {}
   for key, path in reference_paths.items():
       if os.path.exists(path):
           reference_data[key] = match_reference_tiff_to_band_cx(
               tiff_path=path,
               extent_target_lonlat=extent_target,
               target_shape=target_shape,
               target_crs="EPSG:4326",
               label=key,
               plot=True,  # visual QA check
           )
       else:
           print(f"❌ nicht gefunden: {key} -> {path}")
           reference_data[key] = None

   depth_e = reference_data["depth"]   # reference depth [m]
   cx_r    = reference_data["cx"]      # reference TSM [g/m³]
   cp_r    = reference_data["cp"]      # reference Chl-a [µg/L]
   ay_r    = reference_data["ay"]      # reference CDOM [m⁻¹]

**What this cell does:**

Determines the target pixel grid (``extent_target``, ``target_shape``) from the
corrected satellite image, then reprojects and resamples each reference GeoTIFF
onto that grid using ``match_reference_tiff_to_band_cx()``. Missing files are
logged and set to ``None``; ``plot=True`` produces an alignment QA plot per file.

.. list-table:: Reference variables
   :header-rows: 1
   :widths: 15 20 65

   * - Variable
     - Parameter
     - Description
   * - ``depth_e``
     - Water depth
     - In-situ / bathymetric reference [m]; used to optimise SDB coefficients
   * - ``cx_r``
     - *C*\ :sub:`X`
     - Reference TSM concentration [g m\ :sup:`-3`]
   * - ``cp_r``
     - *C*\ :sub:`P`
     - Reference Chl-a concentration [µg L\ :sup:`-1`]
   * - ``ay_r``
     - *a*\ :sub:`Y`
     - Reference CDOM absorption coefficient [m\ :sup:`-1`]

----

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
runs a pixel-wise non-linear optimisation of the Albert & Mobley RTM, using the
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

3.2 Results: Final Parameter Maps & Output Export
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configures the consolidation pipeline, visualises all optimised parameters
per image and band (initial vs. optimised, delta maps), then calls
``run_case_for_image()`` to apply the selected pipeline mode and save
GeoTIFF outputs to disk.

.. code-block:: python

   # Colourmap and axis label per parameter
   parameter_settings = {
       "z_B":      {"cmap": cmocean.cm.deep,   "label": "m"},
       "C_X":      {"cmap": cmocean.cm.matter, "label": "mg/l"},
       "C_P":      {"cmap": cmocean.cm.algae,  "label": "µg/l"},
       "a_Y(λ₀)":  {"cmap": cmocean.cm.turbid, "label": "m⁻¹"},
       "R_B":      {"cmap": "inferno",         "label": "Reflektanz"},
   }

   # Link parameter names to optimised result dicts (from Step 3.1)
   parameter_data = {
       "z_B":      zB_all_bands,
       "C_X":      CX_all_bands,
       "C_P":      CP_all_bands,
       "a_Y(λ₀)":  aY_all_bands,
       "R_B":      Rb_all_bands,
   }

   OUTPUT_ROOT = "/Users/.../cassandra1_test"  # GeoTIFFs saved here

   config = {
       "CASE_MODE":     "mosaic",           # "B3" | "B4" | "mosaic"
       "PIPELINE_MODE": "B",                # "A" | "B" | "C"
       "CONS_BANDS":    ["SR_B3", "SR_B4"],
       "B4_MAX_SHALLOW": 10.0,
       "B3_MAX_DEEP":    15.0,
       "DO_SEAM_SMOOTH_ZB": True,
       "SEAM_SIGMA":    0.8,
       "SEAM_WIDTH_PX": 8,
       "DO_SMOOTH_WQ":  True,
       "WQ_SIGMA":      0.8,
       "BOTTOM_ENDMEMBER_KEYS":  ["Rb_sand", "Rb_ga", "Rb_ba", "Rb_ra"],
       "BOTTOM_CLASS_NAMES":     ["sand", "ga", "ba", "ra"],
       "BOTTOM_MIN_VALID_BANDS": 2,
   }

   SCENE_ID = sdb.get_scene_id_from_globals()

   band_names_per_mission = {
       "Landsat": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"],
   }

   for image_idx in range(1, len(all_corrected_images) + 1):
       sdb.run_case_for_image(
           mission=mission,
           image_idx=image_idx,
           extent_plot=extent,
           scene_id=SCENE_ID,
           output_root=OUTPUT_ROOT,
           case_mode=config["CASE_MODE"],
           pipeline_mode=config["PIPELINE_MODE"],
           band_names_per_mission=band_names_per_mission,
           zB_all_bands=zB_all_bands,
           CX_all_bands=CX_all_bands,
           CP_all_bands=CP_all_bands,
           aY_all_bands=aY_all_bands,
           Rb_all_bands=Rb_all_bands,
           empirical_coefficients=empirical_coefficients,
           config=config,
       )

**What this cell does:**

Applies the configured consolidation pipeline to the optimised band-wise results
and exports the final maps as GeoTIFFs. The behaviour is controlled by two keys:

``CASE_MODE`` — how the final depth map *z*\ :sub:`B` is constructed:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Value
     - Description
   * - ``"B3"``
     - SR_B3 only (green; suits moderate depths with low red-band attenuation).
   * - ``"B4"``
     - SR_B4 only (red; high sensitivity in very shallow water, strongly attenuated at depth).
   * - ``"mosaic"``
     - SR_B4 for *z* ≤ ``B4_MAX_SHALLOW``, SR_B3 for *z* ≥ ``B3_MAX_DEEP``, blended in between. Physically motivated best-of-both-bands approach.

``PIPELINE_MODE`` — level of post-processing applied to band-wise results:

.. list-table::
   :header-rows: 1
   :widths: 10 20 70

   * - Value
     - Name
     - Description
   * - ``"A"``
     - Single-band output
     - No consolidation, no smoothing. Suitable for spectral sensitivity analysis.
   * - ``"B"``
     - Multiband consolidation
     - Results merged across ``CONS_BANDS`` (e.g. median or least-squares). Reduces band-specific noise.
   * - ``"C"``
     - Consolidation + smoothing
     - As B, plus seam-aware Gaussian smoothing for depth (``SEAM_SIGMA``, ``SEAM_WIDTH_PX``) and NaN-aware Gaussian smoothing for water quality parameters (``WQ_SIGMA``).

.. list-table:: Key config parameters
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Default
     - Description
   * - ``CONS_BANDS``
     - ``["SR_B3","SR_B4"]``
     - Bands included in multiband consolidation (Modes B/C)
   * - ``B4_MAX_SHALLOW``
     - ``10.0``
     - Maximum depth [m] at which SR_B4 is used in mosaic mode
   * - ``B3_MAX_DEEP``
     - ``15.0``
     - Minimum depth [m] at which SR_B3 takes over in mosaic mode
   * - ``SEAM_SIGMA``
     - ``0.8``
     - Gaussian sigma [px] for depth seam smoothing (Mode C)
   * - ``SEAM_WIDTH_PX``
     - ``8``
     - Transition width [px] at the B4/B3 seam (Mode C)
   * - ``WQ_SIGMA``
     - ``0.8``
     - Gaussian sigma [px] for water quality smoothing (Mode C)
   * - ``BOTTOM_MIN_VALID_BANDS``
     - ``2``
     - Minimum number of bands required for a valid bottom classification pixel

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
     - Tidal model (e.g. FES2024, TPXO)
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
optimisation and output export. All functions used in ``SDB.ipynb`` are
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
in the Albert & Mobley (2003) radiative transfer model.

.. note::
   Detailed documentation for ``parameters.py`` is not published at this time.