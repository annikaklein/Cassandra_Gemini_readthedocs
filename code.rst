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

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

----

Step 1 – Empirical Coefficients & Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.1 Empirical Coefficients & Backscattering Albedo ω\ :sub:`b`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # [Zelle hier einfügen]

**What this cell does:**

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