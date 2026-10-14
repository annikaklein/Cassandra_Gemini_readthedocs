Methods
=======

Processing Workflow
-------------------

The pipeline implemented in ``CassandraGemini.ipynb`` consists of the following steps:

1. **Step 0 – Preprocessing:** Landsat 8 OLI scene loading (local or Google Earth Engine),
   conversion to BOA and subsurface remote sensing reflectance *R*\ :sub:`rs`, water masking
   (MNDWI), sunglint correction.
2. **Step 1 – Coefficients:** Empirical coefficients (``parameters.py``), backscattering albedo
   ω\ :sub:`b`, deep-water reflectance *R*\ :sub:`rs,∞` and diffuse attenuation *K*\ :sub:`d`.
3. **Step 2 – Initial estimates:** Water depth *z*\ :sub:`B` (2.1), TSM (2.2), Chl-a and CDOM (2.3).
4. **Step 3 – Optimisation:** Pixel-wise joint optimisation of *z*\ :sub:`B`, *C*\ :sub:`X`,
   *C*\ :sub:`P`, *a*\ :sub:`Y` and *R*\ :sub:`B` (Nelder–Mead / least squares).
5. **Water level correction:** Applied externally to the final depth map (see :doc:`code`).

.. todo:: Add workflow flowchart (figure).

Sunglint Correction
-------------------

.. todo:: Describe the linear regression between SWIR and visible bands over optically deep water
   (equation, reference polygon).

Depth Inversion and Optimisation
--------------------------------

.. todo:: Summarise the equations implemented in ``SDB.py`` (see :doc:`theory` for the underlying model).

Validation
----------

.. todo:: Describe reference datasets (airborne LiDAR: Lake Constance, IGKB 2015; One Tree Reef,
   Harris et al. 2023), co-registration, error metrics (RMSE, depth bins) and depth range (≤ 10 m).

Sensitivity Analysis
--------------------

.. todo:: Define the 27 input parameter configurations (V1–V27): which parameter/method choice
   (e.g. ``CX_METHOD``, ``CP_METHOD``, ``AY_METHOD``) differs in each version. Add result table
   (RMSE per version, number of valid pixels).
