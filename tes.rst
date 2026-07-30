Theoretical Background
=======================

This chapter introduces the scientific foundations underlying the Cassandra Gemini
framework. It covers the principles of satellite remote sensing, the optical properties
of natural water bodies, and the physics-based approach to Satellite-Derived Bathymetry
(SDB) — in particular the inversion algorithm of Albert (2004) on which the framework
is based.

Remote Sensing
--------------

Remote sensing is the acquisition of information about the state of the Earth without
direct physical contact. Sensors can be mounted on unmanned aerial vehicles (UAVs),
aircraft or satellites and may be classified as **passive** or **active**. Passive sensors
rely on natural energy sources — primarily reflected sunlight — and include multispectral
cameras and thermal scanners. Active sensors emit their own radiation and measure the
returned signal; typical examples include RADAR and LiDAR (De Jong et al., 2004).

The energy reflected or emitted by a surface is closely linked to its chemical, biological
and physical properties, which govern how electromagnetic radiation is absorbed, scattered
or transmitted. The goal of remote sensing is to exploit these interactions to extract
meaningful information from the recorded signal (Chuvieco, 2020).

Fundamentals of Electromagnetic Radiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Electromagnetic radiation forms the physical foundation of passive remote sensing.
Its behaviour is defined by two parameters: wavelength :math:`\lambda` [m], the distance
between successive wave crests, and frequency :math:`\nu` [Hz], the number of cycles
passing a given point per second. The two are related through the speed of light
:math:`c` [m s\ :sup:`-1`] (Chuvieco, 2020):

.. math::

   c = \lambda \cdot \nu

The energy carried by a single photon follows the Planck–Einstein relation
(Lillesand et al., 2002):

.. math::

   E = h_p \cdot \nu = \frac{h_p \cdot c}{\lambda}

where :math:`h_p = 6.626 \times 10^{-34}` J·s is Planck's constant.
Shorter wavelengths carry higher energy; longer wavelengths (e.g. microwaves) carry less.

When electromagnetic energy interacts with a surface, it is partitioned into reflected
(:math:`E_R`), absorbed (:math:`E_A`) and transmitted (:math:`E_T`) components. Energy
conservation requires (Chuvieco, 2020):

.. math::

   E_I(\lambda) = E_R(\lambda) + E_A(\lambda) + E_T(\lambda)

The **spectral reflectance** :math:`\rho(\lambda)` is the ratio of reflected to incident
radiation (Lillesand et al., 2002):

.. math::

   \rho(\lambda) = \frac{E_R(\lambda)}{E_I(\lambda)} \cdot 100

In aquatic remote sensing, the fundamental radiometric quantity recorded by satellite
sensors is the **remote sensing reflectance** :math:`r_{rs}`, defined as the ratio of
water-leaving radiance :math:`L_w` to downwelling irradiance :math:`E_d`
(Mobley et al., 2016):

.. math::

   r_{rs} = \frac{L_w}{E_d}

Since satellite sensors measure reflectance above the water surface, a correction is
required to obtain the subsurface remote sensing reflectance :math:`R_{rs}`. Albert (2004)
uses a fixed conversion factor applicable to open-ocean conditions:

.. math::

   R_{rs} \approx \frac{r_{rs}}{0.5349}

In the visible spectrum, light penetration depth in water decreases strongly with
increasing wavelength. In optically clear waters, approximate penetration limits are
(Xu et al., 2023):

- **Blue** (440–550 nm): up to ~30 m
- **Green** (500–600 nm): up to ~15 m
- **Red** (600–700 nm): up to ~5 m
- **NIR** (800–1100 nm): up to ~0.5 m

Penetration depth decreases rapidly with increasing turbidity, which shifts the optimal
retrieval wavelength from blue towards green or red (Kalybekova, 2025).

Satellite Sensors
~~~~~~~~~~~~~~~~~

Landsat 8
^^^^^^^^^

The Landsat 8 mission, operated by NASA and the U.S. Geological Survey (USGS), carries
the Operational Land Imager (OLI) and the Thermal Infrared Sensor across eleven spectral
bands. Key characteristics (National Aeronautics and Space Administration, 2025a, 2025b):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Parameter
     - Value
   * - Spatial resolution
     - 30 m (visible–NIR–SWIR)
   * - Spectral resolution
     - 30–100 nm
   * - Spectral range
     - 0.43–12 µm
   * - Radiometric resolution
     - 12 bit
   * - Temporal resolution
     - 16 days
   * - Viewing geometry
     - Near-nadir

Raw Landsat 8 images store the measured radiance as digital numbers (DNs). Conversion
to surface reflectance is performed as (Costa-Filho et al., 2024):

.. math::

   r_{rs} = 0.0000275 \cdot DN_i - 0.20

where :math:`DN_i` is the recorded digital number for band :math:`i`.
Level-2 products (atmospherically corrected) are produced using the LaSRC algorithm
developed by USGS/NASA (U.S. Geological Survey, 2025).

Sentinel-2
^^^^^^^^^^

The Sentinel-2 constellation (ESA Copernicus Programme) operates two satellites
(2A and 2B, plus 2C since 2024), each carrying the MultiSpectral Instrument (MSI)
with 13 spectral bands. Spatial resolution is 10 m, 20 m or 60 m depending on the band;
temporal resolution is 5 days at the equator (European Space Agency, 2025a, 2025b).
While Sentinel-2 offers finer spatial and spectral detail, Landsat 8 has been shown to
produce more consistent bathymetric results in cross-sensor comparisons and is therefore
the primary sensor in Cassandra Gemini.

Optical Properties of Water Bodies
-----------------------------------

The optical properties of water bodies are determined by their interaction with
electromagnetic radiation in the visible and near-infrared (NIR) parts of the spectrum.
Clear water reflects most strongly near 450–500 nm and absorbs increasingly towards
the red and NIR. In shallow waters, bottom reflectance adds a further contribution
to the water-leaving signal, making depth retrieval from satellites feasible.

Waters are commonly classified into two categories (Prieur and Sathyendranath, 1981):

- **Case-1 waters**: optical properties dominated by phytoplankton and its by-products;
  typical of open-ocean environments.
- **Case-2 waters**: optically more complex; found in coastal zones, estuaries and inland
  waters, where Total Suspended Matter (TSM), Phytoplankton Chlorophyll-a (Chl) and
  Coloured Dissolved Organic Matter (CDOM) jointly shape the spectral signal
  (Albert, 2004; Gege, 1994; Schalles, 2006).

Understanding the optical properties of Case-2 waters is essential for accurate
bathymetric retrieval, as multiple constituents contribute simultaneously to the
remotely sensed signal.

Inherent Optical Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inherent optical properties (IOPs) describe the absorption and scattering characteristics
of water and its constituents independently of the ambient light field (Laanen, 2007).
The two fundamental IOPs are:

- **Absorption coefficient** :math:`a(\lambda)` [m\ :sup:`-1`]: rate of absorption of
  light per unit path length.
- **Scattering coefficient** :math:`b(\lambda)` [m\ :sup:`-1`]: rate of scattering per
  unit path length.

The total absorption and backscattering coefficients are the sum of contributions from
pure water (:math:`W`), Chl (:math:`P`), TSM (:math:`X`) and CDOM (:math:`Y`)
(Albert, 2004):

.. math::

   a(\lambda) = a_W(\lambda) + a_P(\lambda) + a_X(\lambda) + a_Y(\lambda)

.. math::

   b_b(\lambda) = b_{b,W}(\lambda) + b_{b,P}(\lambda) + b_{b,X}(\lambda) + b_{b,Y}(\lambda)

The **backscattering ratio** :math:`\omega_b`, the fraction of total scattering directed
back towards the surface and detectable by the satellite, is defined as (Albert, 2004):

.. math::

   \omega_b = \frac{b_b}{a + b_b}

Total Suspended Matter (TSM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TSM includes inorganic particles (clay, silt) that primarily increase scattering and
raise water-leaving reflectance across all wavelengths. Concentrations in Case-2 waters
typically range from 0.6 to 200 mg l\ :sup:`-1` (Wei et al., 2022).
Empirical retrieval methods include (Ficek et al., 2011; Parwati et al., 2023):

.. math::

   C_{X,\mathrm{Ficek}} = 5590 \cdot R_{rs}(798)^{0.95}

In the Albert (2004) framework, :math:`C_X` is derived analytically from the
radiative transfer formulation using reflectance in the NIR (~760 nm).

Phytoplankton Chlorophyll-a (Chl)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Chlorophyll-a contributes primarily to absorption in the blue and red regions, with
a characteristic absorption dip near 676 nm. Typical concentrations in Case-2 waters
range from 1.4 to 13.4 µg l\ :sup:`-1` (Wei et al., 2022). Empirical retrieval models
include (Ficek et al., 2011; Abbas et al., 2019):

.. math::

   C_{P,\mathrm{Ficek}} = 6.432 \cdot \exp(4.556 \cdot K), \quad
   K = \frac{\max R_{rs}(695{-}720) - R_{rs}(670)}{\max R_{rs}(695{-}720)}

Coloured Dissolved Organic Matter (CDOM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CDOM (also called yellow matter or *Gelbstoff*) is the optically active fraction of
dissolved organic material. It absorbs strongly below 500 nm and gives inland and
coastal waters their characteristic brownish colour (Brezonik et al., 2015; Laanen, 2007).
Unlike TSM and Chl, CDOM is quantified by its spectral absorption coefficient
:math:`a_Y(\lambda)` [m\ :sup:`-1`]. Empirical formulations include
(Ficek et al., 2011; Wong et al., 2020):

.. math::

   a_{Y,\mathrm{Ficek}}(440) = 3.65 \cdot \left(\frac{R_{rs}(570)}{R_{rs}(655)}\right)^{-1.93}

Bottom Reflectance
^^^^^^^^^^^^^^^^^^

In shallow water, a fraction of downwelling light reaches and reflects off the seafloor.
The bottom reflectance coefficient :math:`R_B` is strongly wavelength-dependent and
varies with substrate composition. Typical endmembers include coral sand, and green,
brown and red algae (Maritorena et al., 1994), each exhibiting distinct spectral features —
coral sand shows continuously increasing reflectance towards the NIR, while algal spectra
display pigment-related absorption features near 550 nm and 675 nm (Albert, 2004).

Apparent Optical Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apparent optical properties (AOPs) describe the radiometric characteristics of a water
body that result from the interaction between IOPs and the ambient light field geometry.
Unlike IOPs, AOPs depend on external factors such as sun angle, viewing geometry and
atmospheric conditions (Mobley, 1994; Laanen, 2007).

The most important AOP in SDB is the **remote sensing reflectance** :math:`R_{rs}`
[sr\ :sup:`-1`], which describes the water-leaving radiance per unit downwelling irradiance
detectable at the sensor.

The **diffuse attenuation coefficient** :math:`K_d` [m\ :sup:`-1`] describes how rapidly
light is attenuated with depth due to absorption and scattering. Following Albert (2004):

.. math::

   K_d = \kappa_0 \cdot \frac{a + b_b}{\cos \theta_s}

where :math:`\kappa_0` is an empirical coefficient and :math:`\theta_s` is the solar
zenith angle below the water surface. Because light is refracted at the air–water
interface, subsurface angles are derived from above-surface angles via Snell's law using
the refractive index of water :math:`n_W = 1.33`.

Satellite-Derived Bathymetry
-----------------------------

SDB refers to the estimation of water depth from satellite sensors by exploiting the
interaction of light with the water column and seafloor (Ashphaq et al., 2021; He et al., 2024).
It is particularly relevant for optically shallow coastal zones, inland lakes, estuaries
and coral reef systems — environments where the seafloor remains visible from space.

Passive SDB approaches fall into several categories:

- **Empirical / Machine Learning**: statistical relationships between reflectance band
  ratios and in-situ depths. Easy to implement but require calibration data and have
  limited transferability across sites (Kalybekova, 2025).
- **Physics-based inversion**: invert the radiative transfer model (RTM) to match
  simulated and observed reflectance. No in-situ calibration required; physically
  interpretable and transferable (Albert, 2004).
- **Photogrammetric**: depth from stereo satellite imagery via triangulation. Requires
  high-resolution imagery and calm conditions (Chénier et al., 2018).
- **Wave-based**: depth from wave dispersion kinematics. Independent of water clarity
  but coarse spatial resolution (He et al., 2024).

Cassandra Gemini implements the physics-based approach.

Physics-Based Approach
~~~~~~~~~~~~~~~~~~~~~~~

Physics-based SDB simulates the propagation of solar radiation through the atmosphere,
water column and seafloor using the RTM. The observed spectral radiance
:math:`L(\lambda)` at the satellite can be decomposed as (Vinayaraj et al., 2016):

.. math::

   L(\lambda) = V(\lambda) + B(\lambda) + S(\lambda) + A(\lambda)

where :math:`V(\lambda)` is in-water scattering radiance, :math:`B(\lambda)` is bottom
reflection radiance, :math:`S(\lambda)` is water surface reflection radiance and
:math:`A(\lambda)` is atmospheric scattering radiance.

The volume term :math:`V(\lambda)` is strongly influenced by TSM, Chl, CDOM and pure
water absorption. The bottom term :math:`B(\lambda)` dominates the signal in shallow
waters and vanishes in optically deep water where absorption dominates (Lee et al., 1999).

The essential principle of physics-based SDB is **RTM inversion**: given the observed
satellite radiance, the unknown water depth, water quality parameters and bottom
reflectance are retrieved by iteratively adjusting model parameters until simulated and
measured reflectance converge (Albert, 2004; Hartmann et al., 2021).

Albert (2004) Algorithm
~~~~~~~~~~~~~~~~~~~~~~~~

The Albert (2004) algorithm provides an analytical and iterative inversion framework for
the simultaneous retrieval of water depth :math:`z_B`, TSM :math:`C_X`,
Chl :math:`C_P`, CDOM :math:`a_Y(\lambda_0)` and bottom reflectance :math:`R_B` from
a single multispectral scene.

The simulated remote sensing reflectance is modelled as:

.. math::

   R_{rs} = R_{rs,\infty} \cdot \left(1 - A_{rs,1} \cdot \exp\!\left(-K_d
   \left(1 + \tfrac{1}{\cos\theta_v}\right) z_B\right)\right)
   + A_{rs,2} \cdot \frac{R_B}{\pi} \cdot \exp\!\left(-K_d
   \left(1 + \tfrac{1}{\cos\theta_v}\right) z_B\right)

where :math:`R_{rs,\infty}` is the deep-water reflectance (unaffected by the bottom),
:math:`\theta_v` is the viewing angle below the water surface, and
:math:`A_{rs,1}`, :math:`A_{rs,2}` are empirical coefficients from Albert (2004).

Inverting for depth yields:

.. math::

   z_B = \frac{1}{K_d \left(1 + \tfrac{1}{\cos\theta_v}\right)}
   \cdot \ln\!\left(\frac{A_{rs,1} \cdot R_{rs,\infty} - A_{rs,2} \cdot \tfrac{R_B}{\pi}}
   {R_{rs,\infty} - R_{rs}}\right)

This initial depth estimate uses the 600–650 nm wavelength interval, where bottom
influence is sufficiently strong for reliable inversion in shallow waters (< 10 m).

**Inversion workflow** (Albert, 2004):

1. Measure or simulate :math:`R_{rs}` from the satellite scene.
2. Define a set of candidate bottom types :math:`R_{B,i}`.
3. Select parameters to optimize: :math:`z_B`, :math:`C_X`, :math:`C_P`,
   :math:`a_Y`, :math:`\theta_v`, :math:`\theta_s`, :math:`f_{a,i}`.
4. Compute analytical initial estimates for all parameters.
5. Pre-optimize in NIR/blue bands (up to 100 iterations).
6. Apply the **Nelder–Mead Simplex Algorithm** over 400–800 nm to minimize the
   residual between simulated and measured :math:`R_{rs}`.

The method performs best within the 450–750 nm spectral window and for depths below
approximately 10 m. Beyond ~15 m, bottom influence vanishes and retrieval errors exceed
60 % (Albert, 2004). Typical mean relative errors under realistic optical conditions are
approximately 5–10 % for depth, 1–3 % for TSM, 7–9 % for Chl and 1–2 % for CDOM
(Albert, 2004).

.. note::
   The reliable retrieval range of the implemented model is limited to approximately
   **10 m water depth**. Beyond this, the bottom signal is largely lost in the
   water-leaving reflectance and retrieval becomes unreliable.
