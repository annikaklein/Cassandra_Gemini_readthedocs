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

1.2 Metadata Extraction & Angle Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

1.3 Downward Diffuse Attenuation Coefficient & Deep Water Reflectance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

Step 2 – Water Constituent Retrieval
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2.1 Water Depth
^^^^^^^^^^^^^^^

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

2.2 Total Suspended Matter
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

2.3 Phytoplankton Chlorophyll-a and CDOM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

Step 3 – Parameter Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

Step 4 – Tide Correction
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

sdb.py
------

*Dokumentation folgt.*

----

parameters.py
-------------

*Dokumentation folgt.*