Background
==========

Why Satellite-Derived Bathymetry?
---------------------------------

Coastal regions worldwide are exposed to sea-level rise and ongoing shoreline erosion and
accretion (Luijendijk et al., 2018). Assessing these impacts and planning adaptation requires
numerical hydrodynamic and morphological models, whose performance depends on accurate
bathymetry (Pacheco et al., 2015; Rasquin et al., 2020; On Chan et al., 2024).

Traditional surveys with shipborne acoustic systems are accurate but time-consuming,
resource-intensive and limited in shallow or hazardous waters, where vessel access is
restricted and the sonar footprint narrows with decreasing depth (Ashphaq et al., 2021).
Despite international efforts such as Seabed 2030, only about 30 % of the ocean floor has been
charted at adequate resolution, and the gap is largest in the optically shallow nearshore zone
(Cesbron et al., 2021).

**Satellite-Derived Bathymetry (SDB)** closes this gap with freely available multispectral
imagery: water depth is estimated from the signal that sunlight leaves after passing through
the water, reflecting off the seabed and returning to the sensor.

Empirical vs. physics-based methods
-----------------------------------

- **Empirical methods** relate spectral band ratios to in-situ depths (Stumpf et al., 2003).
  They are simple, but require site-specific calibration data.
- **Physics-based methods** invert the radiative transfer equation for the atmosphere, water
  column and seafloor (Albert 2004; Lee et al., 1999). They are physically interpretable and
  need no depth calibration. They are especially relevant for **Case-2 waters** (coastal,
  estuarine, inland), where TSM, Chl-a and CDOM jointly shape the signal.

Commercial physics-based products (e.g. EOMAP) are operationally mature but proprietary: they
cannot be inspected, reproduced or verified, and are sold per survey, which puts them out of
reach for many institutions. Existing open tools (e.g. WASI-2D, Gege 2005) are distributed as
closed executables and lack integration with automated satellite data pipelines.

What Cassandra Gemini provides
------------------------------

*Cassandra Gemini* is an open, physics-based inversion framework that recovers water depth,
TSM, Chl-a and CDOM from a single multispectral Landsat 8 scene without in-situ calibration.
It is evaluated at two sites spanning the range of water clarity — Lake Constance (turbid) and
One Tree Reef (clear) — against airborne LiDAR. It reaches RMSE = 0.38 m and 0.79 m for depths
up to 10 m, and a systematic analysis of 27 parameter configurations identifies TSM as the
dominant control on accuracy. See :doc:`bsp1`, :doc:`bsp2` and :doc:`results`.

.. todo:: Add the cited references (Luijendijk 2018, Pacheco 2015, Rasquin 2020, On Chan 2024,
   Cesbron 2021, Stumpf 2003, Lee 1999) to :doc:`citations`.
