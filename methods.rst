Methods
=======

This chapter documents the complete processing pipeline of the *Cassandra Gemini*
framework: satellite data and preprocessing, the alternative parameterisation
pathways, the physics-based inversion, and the validation against reference data.

.. tikz:: Processing pipeline. Step numbers correspond to the cells of ``CassandraGemini.ipynb``.
   :libs: positioning,calc,fit,arrows.meta,backgrounds
   :align: center

   \begin{tikzpicture}[
     node distance=1cm and 4.33cm,
     box/.style={draw, rectangle, minimum width=0.7\tw, minimum height=1cm, align=center},
     smallbox/.style={draw, rectangle, minimum width=0.45\tw, minimum height=0.8cm, align=center, fill=white},
     smallbigbox/.style={draw, rectangle, minimum width=0.33\tw, minimum height=0.8cm, align=center, fill=white},
     arrow/.style={-{Stealth}, thick}
   ]
   \sffamily
   \node[smallbox] (PreData) {1. Preprocessed Data};
   \node[smallbigbox, below left=of PreData.south east]  (EmpCoe) {1.1 Empirical Coefficients};
   \node[smallbigbox, below right=of PreData.south west] (Meta)   {1.2 Extract Metadata};
   \node[smallbigbox, minimum height=2.5\baselineskip, inner sep=2pt, below=of EmpCoe, yshift=0.5cm] (low1)
         {1.1.2. Calculate Backscattering\\Albedo $\omega_b$};
   \node[smallbigbox, minimum height=2.5\baselineskip, inner sep=2pt, below=of Meta, yshift=0.5cm] (low2)
         {1.2.2. Angle\\Conversion};
   \coordinate (midlow) at ($(low1)!0.5!(low2)$);
   \node[box, below=of midlow, yshift=-0.5cm] (bottom)
     {1.3 Calculate downward diffuse attenuation coefficient $K_d$\\
      and deep water remote sensing reflectance $R_{rs,\infty}$};
   \draw[arrow] (PreData.south) -- ++(0,-0.5) -| (EmpCoe.north);
   \draw[arrow] (PreData.south) -- ++(0,-0.5) -| (Meta.north);
   \draw[arrow] (EmpCoe.south) -- (low1.north);
   \draw[arrow] (Meta.south)   -- (low2.north);
   \draw[arrow] (low1.south)   -- ++(0,-0.5) -| (bottom.north);
   \draw[arrow] (low2.south)   -- ++(0,-0.5) -| (bottom.north);

   \node (zb_label) [below=of bottom, yshift=0.33cm] {2.1. \textbf{Water Depth}};
   \node[smallbox] (zbdatan) [below=of zb_label, yshift=0.75cm] {Calculate water depth $z_B$\\(single band SR\_B4)};
   \node (cx_label) [below=of zbdatan] {2.2. \textbf{Total Suspended Matter}};
   \node[smallbox] (cxdatan) [below=of cx_label, yshift=0.75cm]
        {Estimate Total Suspended Matter concentration $C_X$\\using Method A, E1 or E2};
   \node (cp_label) [below=of cxdatan] {2.3. \textbf{Chlorophyll-a and CDOM}};
   \node[smallbox] (cpdatan) [below=of cp_label, yshift=0.75cm]
        {Estimate Chlorophyll-a concentration $C_P$\\and CDOM absorption $a_Y$\\
         jointly (a) or individually (b)};
   \node (opt_label) [below=of cpdatan] {3. \textbf{Parameter Optimization}};
   \node[smallbox] (opt1) [below=of opt_label, yshift=0.75cm]
        {Optimize $z_B$, $C_X$, $C_P$, $a_Y$ and $R_B$};
   \node[smallbox, rotate=90] (tidegauge) [right=of cp_label] {Tidegauge};
   \node[smallbox] (tidecorrected) [below=of opt1, yshift=0.25cm] {4. Tidecorrected $z_B$};

   \begin{pgfonlayer}{background}
     \node[box, blue!70, fill=blue!5, thick, inner sep=0.3cm, rounded corners,
           fit={(zb_label.north) (zbdatan.west) (zbdatan.east) (zbdatan.south)}] (zb_gesamt) {};
     \node[box, orange!70, fill=orange!5, thick, inner sep=0.3cm, rounded corners,
           fit={(cx_label.north) (cxdatan.west) (cxdatan.east) (cxdatan.south)}] (cx_gesamt) {};
     \node[box, green!70, fill=green!5, thick, inner sep=0.3cm, rounded corners,
           fit={(cp_label.north) (cpdatan.west) (cpdatan.east) (cpdatan.south)}] (cp_gesamt) {};
     \node[box, red!70, fill=red!5, thick, inner sep=0.3cm, rounded corners,
           fit={(opt_label.north) (opt1.west) (opt1.east) (opt1.south)}] (opt_gesamt) {};
   \end{pgfonlayer}

   \draw[arrow] (bottom.south)    -- (zb_gesamt.north);
   \draw[arrow] (zb_gesamt.south) -- (cx_gesamt.north);
   \draw[arrow] (cx_gesamt.south) -- (cp_gesamt.north);
   \draw[arrow] (cp_gesamt.south) -- (opt_gesamt.north);
   \draw[arrow] (Meta.east)    -| (tidegauge);
   \draw[arrow] (tidegauge)    |- (tidecorrected);
   \draw[arrow] (opt1)         -- (tidecorrected);
   \end{tikzpicture}

Satellite Data and Preprocessing
--------------------------------

Sensor and data acquisition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Imagery is taken from Landsat 8 OLI (Level-2 surface reflectance, bands SR_B1–SR_B6,
30 m). Scenes are retrieved through the Google Earth Engine API or, alternatively,
downloaded from USGS EarthExplorer for local processing. The study areas are defined by
bounding boxes:

- **Lake Constance:** western sub-basin (Untersee, 6.38 km²), 8.988–9.020°E, 47.685–47.708°N
- **One Tree Reef:** entire reef system (27.88 km²), 152.036–152.101°E, 23.478–23.516°S

Scenes were selected as close as possible to the reference surveys (Lake Constance:
29 March 2014, LiDAR survey 29–30 March 2014; One Tree Reef: 9 October 2018, LiDAR survey
8 October 2018) and filtered by cloud cover (< 5 %), medium cloud, thin cirrus and high
cloud cover (< 1 % each) and solar zenith angle (< 60°). Each scene was inspected visually
for cloud contamination.

Data are stored in EPSG:4326. Metric operations (resampling, interpolation) are performed
after temporary reprojection to the local UTM zone (Lake Constance: EPSG:32632; One Tree
Reef: EPSG:32756) with bilinear interpolation on a 30 m × 30 m grid; final products are
reprojected back to EPSG:4326.

Step 0 – Preprocessing
~~~~~~~~~~~~~~~~~~~~~~

Digital numbers are converted to surface reflectance (Costa-Filho et al., 2024):

.. math::

   \rho_{BOA,i} = 0.0000275 \cdot DN_i - 0.20

The above-surface remote-sensing reflectance is :math:`r_{rs} = \rho_{BOA}/\pi`
(Mobley et al., 2016). The subsurface remote-sensing reflectance follows (Lee et al., 2002):

.. math::

   R_{rs} = \frac{r_{rs}}{T + \vartheta \cdot Q \cdot r_{rs}}

with :math:`T = 0.52` and :math:`\vartheta \cdot Q = 1.7` (nadir view, optically deep water).

Water pixels are identified with the MNDWI (Xu 2006):

.. math::

   \mathrm{MNDWI} = \frac{\rho_{Green} - \rho_{SWIR}}{\rho_{Green} + \rho_{SWIR}}

using SR_B3 (green) and SR_B6 (SWIR). The threshold is set via ``mndwi_threshold``
(0.2 in the publication; 0.25 in the One Tree Reef example notebook).

**Sunglint correction** follows the linear regression approach of Hochberg et al. (2003)
and Harmel et al. (2018). SWIR brightness is assumed to represent surface reflection only.
A regression between each visible band :math:`q` and the SWIR band is fitted over a
user-defined, homogeneous, optically deep water area:

.. math::

   R'_{rs,q} = R_{rs,q} - r_q \cdot \left(R_{rs,SWIR} - R_{\min,SWIR}\right)

where :math:`r_q` is the regression slope and :math:`R_{\min,SWIR}` the minimum SWIR
reflectance over glint-free pixels. Reference areas used: Lake Constance 0.004 km²
(9.024–9.033°E, 47.691–47.695°N); One Tree Reef 0.011 km² (152.057–152.062°E,
23.485–23.487°S).

Step 1.1 – Empirical coefficients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Coefficients are read from ``parameters.py``: :math:`a_W`, :math:`b_{b,W}`, :math:`a^*_P`,
:math:`a^*_Y`, :math:`b^*_{b,X}` and the bottom reflectance spectra :math:`R_B`
(sand, silt, green/brown/red algae). Total absorption and backscattering decompose into
the contributions of pure water (W), Chl-a (P), TSM (X) and CDOM (Y) (Albert 2004):

.. math::

   a(\lambda) = a_W + a_P + a_X + a_Y, \qquad
   b_b(\lambda) = b_{b,W} + b_{b,P} + b_{b,X} + b_{b,Y}

with :math:`b_{b,W} = b_W/2`. The backscattering albedo is

.. math::

   \omega_b = \frac{b_b}{a + b_b}

Step 1.2 – Metadata and angle conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Acquisition time, solar zenith angle :math:`\theta_s^+` and per-band viewing angle
:math:`\theta_v^+` are extracted from the scene metadata. Both are converted to below-water
angles :math:`\theta_s`, :math:`\theta_v` with Snell's law (:math:`n_w = 1.33`).

Step 1.3 – Optical parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The downward diffuse attenuation coefficient :math:`K_d` and the deep-water reflectance
:math:`R_{rs,\infty}` are computed from :math:`\omega_b`, :math:`\theta_s`, :math:`a_W` and
:math:`b_{b,W}` and passed on to Steps 2 and 3.

Parameterisation Pathways
-------------------------

Step 2.1 – Depth estimation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If reference bathymetry is available it can be imported directly. Otherwise the initial
depth is estimated from :math:`R_{rs}` of a single band (SR_B4) with an artificial bottom
reflectance :math:`R_B = 0.1` (Albert 2004):

.. math::
   :label: depth

   z_B = \frac{1}{K_d \left(1 + \frac{1}{\cos\theta_v}\right)}
   \ln\left(\frac{A_{rs,1} R_{rs,\infty} - A_{rs,2} \frac{R_B}{\pi}}
   {R_{rs,\infty} - R_{rs}}\right)

Depth is positive downwards.

Step 2.2 – Total Suspended Matter :math:`C_X`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Method A (Albert 2004, SR_B5, 760 nm).** The bottom-corrected upward reflectance is

.. math::

   R_u = \frac{R_{rs} - A_{rs,2}\frac{R_B}{\pi}\exp\left(-K_d\left(1+\frac{1}{\cos\theta_v}\right)z_B\right)}
   {f^-\left(1 - A_{rs,1}\exp\left(-K_d\left(1+\frac{1}{\cos\theta_v}\right)z_B\right)\right)},
   \qquad f^- = \frac{R_{rs,\infty}}{\omega_b}

.. math::

   C_{X,A} = \frac{R_u\left(a_W + \tfrac12 b_{b,W}\right) - \tfrac12 b_{b,W}}{b^*_{b,X}\,(1 - R_u)}

**Method E1 (Ficek et al. 2011, SR_B5):**

.. math::

   C_{X,F} = 5590 \cdot R_{rs}(798)^{0.95}

**Method E2 (Parwati et al. 2023, SR_B4):**

.. math::

   C_{X,P} = 8.1429 \cdot \exp\left(23704 \cdot R_{rs,red}\right)

Step 2.3 – Chlorophyll-a :math:`C_P` and CDOM :math:`a_Y`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:math:`C_P` and :math:`a_Y` are estimated either jointly (Method A) or individually
(Methods E1/E2).

.. tikz:: (a) Iterative joint approach (Method A) and (b) independent approach (Methods E1/E2).
   :libs: positioning,calc,fit,arrows.meta,backgrounds
   :align: center

   \begin{tikzpicture}[
     smallbox/.style={draw, rectangle, minimum width=6.4cm, minimum height=1cm, align=center, fill=white},
     arrow/.style={-{Stealth}, thick}]
   \sffamily
   \node[smallbox, fill=gray!15, minimum width=10cm] (in) at (0,0) {Inputs: $R_{rs}$, $z_B$, $C_X$, $K_d$, $R_{rs,\infty}$, $\omega_b$};
   \node[smallbox] (a1) at (-4.1,-3.2) {Stage 1: iterate total absorption $a$\\{\small (SR\_B1, SR\_B2; $a_\mathrm{init}=0.75$\,m$^{-1}$, $\varepsilon=0.001$)}};
   \node[smallbox] (a2) at (-4.1,-5.2) {Stage 2: pixelwise least-squares fit\\of $C_P$ and $a_Y$};
   \node[smallbox] (e1) at (4.1,-3.2) {$C_P$: E1 Ficek et al.\ (2011)\\or E2 Abbas et al.\ (2019)};
   \node[smallbox] (e2) at (4.1,-5.2) {$a_Y$: E1 Ficek et al.\ (2011)\\or E2 Wong et al.\ (2020)};
   \node[smallbox, fill=gray!15, minimum width=8cm] (out) at (0,-8.2) {Maps of $C_P$ and $a_Y$\\(initial values for Step 3)};
   \begin{pgfonlayer}{background}
     \node[draw=green!60!black, fill=green!5, thick, rounded corners, inner sep=0.3cm,
           fit=(a1)(a2)] (fa) {};
     \node[draw=green!60!black, fill=green!5, thick, rounded corners, inner sep=0.3cm,
           fit=(e1)(e2)] (fb) {};
   \end{pgfonlayer}
   \node[font=\sffamily\bfseries\small, anchor=south west] at ([xshift=-0.1cm]fa.north west) {(a) Method A -- joint, iterative};
   \node[font=\sffamily\bfseries\small, anchor=south west] at ([xshift=-0.1cm]fb.north west) {(b) Methods E1/E2 -- individual};
   \draw[arrow] (in.south) -- ++(0,-0.4) -| ([yshift=0.6cm]fa.north);
   \draw[arrow] (in.south) -- ++(0,-0.4) -| ([yshift=0.6cm]fb.north);
   \draw[thick] ([yshift=0.6cm]fa.north) -- (fa.north);
   \draw[thick] ([yshift=0.6cm]fb.north) -- (fb.north);
   \draw[arrow] (a1) -- (a2);
   \draw[arrow] (fa.south) -- ++(0,-0.6) -| (out.north);
   \draw[arrow] (fb.south) -- ++(0,-0.6) -| (out.north);
   \end{tikzpicture}

**Method A – joint inversion (Albert 2004).** The simulated reflectance is

.. math::
   :label: rrs_sim

   R_{rs,sim} = R_{rs,\infty}\left(1 - A_{rs,1}e^{-(K_d + K_{u,W})z_B}\right)
   + A_{rs,2}\frac{R_B}{\pi}e^{-(K_d + K_{u,B})z_B}

.. math::

   K_{u,W} = \frac{(a+b_b)(1+\omega_b)^{k_{1u}}\left(1+\frac{k_{2u}}{\cos\theta_s}\right)}{\cos\theta_v},
   \qquad
   K_{u,B} = \frac{(a+b_b)(1+\omega_b)^{k_{1b}}\left(1+\frac{k_{2b}}{\cos\theta_s}\right)}{\cos\theta_v}

Stage 1 iterates the total absorption :math:`a` (start 0.75 m⁻¹, relative error
:math:`\varepsilon = 0.001`, max. 3000 iterations) on bands SR_B1 and SR_B2. Stage 2
fits :math:`a_Y` and :math:`C_P` pixel-wise by least squares over all bands
(``scipy.optimize.least_squares`` instead of the Nelder–Mead simplex of the original
formulation). The framework is therefore an adaptation, not a one-to-one reproduction,
of Albert (2004).

**Chl-a, individual retrieval**

- E1 (Ficek et al. 2011, SR_B4/SR_B5):
  :math:`C_{P,F} = 6.432\,\exp(4.556\,K)`, with
  :math:`K = \frac{\max R_{rs}(695\text{–}720) - R_{rs}(670)}{\max R_{rs}(695\text{–}720)}`
- E2 (Abbas et al. 2019, SR_B3/SR_B4):
  :math:`C_{P,Ab} = 10\exp(e_0 + e_1K + e_2K^2 + e_3K^3 + e_4K^4)`, with
  :math:`K = \ln(R_{rs,green}/R_{rs,red})`

**CDOM, individual retrieval**

- E1 (Ficek et al. 2011, SR_B3/SR_B4):
  :math:`a_{Y,F}(440) = 3.65\,\left(R_{rs}(570)/R_{rs}(655)\right)^{-1.93}`
- E2 (Wong et al. 2020, SR_B2/SR_B4):
  :math:`a_{Y,W}(440) = 0.843\,\left(R_{rs}(B2)/R_{rs}(B4)\right)^{-1.1}`

The 27 configurations
~~~~~~~~~~~~~~~~~~~~~

Each of :math:`C_X`, :math:`C_P` and :math:`a_Y` can be derived by any of the three
pathways (A, E1, E2), giving :math:`3^3 = 27` versions. Version numbering: the index runs
fastest over :math:`a_Y`, then :math:`C_P`, then :math:`C_X`
(V1–V9: :math:`C_{X,A}`, V10–V18: :math:`C_{X,E1}`, V19–V27: :math:`C_{X,E2}`).

.. list-table::
   :header-rows: 1
   :widths: 15 28 28 29

   * - Version
     - :math:`C_X`
     - :math:`C_P`
     - :math:`a_Y`
   * - V1
     - A
     - A
     - A  (*Albert-based* benchmark)
   * - V6
     - A
     - E1
     - E2  (**Cassandra Gemini**, best accuracy at both sites)
   * - V2–V5, V7–V9
     - A
     - A / E1 / E2
     - A / E1 / E2
   * - V10–V18
     - E1
     - A / E1 / E2
     - A / E1 / E2
   * - V19–V27
     - E2
     - A / E1 / E2
     - A / E1 / E2

(Full table: V\ *n* with *n* = 9·(i\ :sub:`X`) + 3·(i\ :sub:`P`) + i\ :sub:`Y` + 1, where
A = 0, E1 = 1, E2 = 2; e.g. V6 = (0, 1, 2) → A / E1 / E2.)

Physics-Based Inversion Model
-----------------------------

The inversion applies the radiative transfer formulation of Albert (2004) independently
to each band (SR_B1–SR_B6). For each pixel, :math:`z_B`, :math:`C_X`, :math:`C_P`,
:math:`a_Y` and :math:`R_B` are optimised simultaneously by minimising

.. math::

   \varepsilon_\lambda = \left(R_{rs,meas}(\lambda) - R_{rs,sim}(\lambda)\right)^2

with :math:`R_{rs,sim}` from :eq:`rrs_sim`. The optimiser is ``scipy.optimize.least_squares``;
start values come from Step 2. Bounds:

.. math::

   \mathbf{p}_{\min} = [0,0,0,0,0], \qquad \mathbf{p}_{\max} = [30, 100, 100, 5, 0.7]

for :math:`z_B` [m], :math:`C_X` [mg l⁻¹], :math:`C_P` [µg l⁻¹], :math:`a_Y` [m⁻¹] and
:math:`R_B` [–]. Convergence: cost change < 10⁻⁸ or maximum 600 function evaluations.
Pixels that do not converge are re-initialised with perturbed start values; remaining
non-converging pixels are masked.

**Consolidation of the per-band results.** :math:`z_B` is taken from the SR_B4 retrieval;
:math:`C_X`, :math:`C_P` and :math:`a_Y` are the pixel-wise median of SR_B3 and SR_B4;
:math:`R_B` is classified into bottom types (sand, green/brown/red algae, silt) by the
minimum multi-band squared error against reference spectra (at least two valid bands).
All outputs are exported as GeoTIFF (EPSG:4326).

.. note::
   The released notebook currently writes the SR_B4 depth map (``CASE_B4``, pipeline mode ``A``);
   see :doc:`code`.

Reference Data and Validation
-----------------------------

**Lake Constance.** Airborne LiDAR bathymetry (Riegl VQ-820-G, 532 nm, 256 kHz,
20–40 points m⁻²) was flown on 29–30 March 2014 (Wessels et al., 2015), gridded to 3 m and
referenced to the long-term mean water level at Konstanz (394.85 m NHN). On 29 March 2014 the
level was 0.35 m below the 30-year mean (Berlingen gauge: 394.94 m NHN, 0.44 m below its
mean). Daily gauge deviations were applied as vertical corrections. Data: IGKB (2015),
`PANGAEA <https://doi.org/10.1594/PANGAEA.855987>`_.

**One Tree Reef.** Airborne topo-bathymetric LiDAR (Riegl VQ-820-G at 284/522 kHz plus
Riegl Q680i-S, 25–30 points m⁻²) on 8 October 2018 (Harris et al., 2023), 0.25 m DEM, vertical
accuracy ±0.1 m, referenced to MSL. Because the scene (9 October 2018) and the survey differ in
tidal stage and no gauge is nearby, tidal offsets from the FES2022 model were applied.
Data: `PANGAEA <https://doi.org/10.1594/PANGAEA.963918>`_.

Both LiDAR grids were resampled bilinearly to the 30 m Landsat grid. In addition, the EOMAP
WATCOR-X product (Sentinel-2, 15 May 2017–22 October 2018; Great Barrier Reef Marine Park
Authority Reef GeoHub) is used as an optical reference at One Tree Reef.

Accuracy metrics
~~~~~~~~~~~~~~~~

For :math:`N` valid pixel pairs (reference :math:`z_i`, estimate :math:`\hat z_i`):

.. math::

   R^2 = 1 - \frac{\sum (z_i-\hat z_i)^2}{\sum (z_i-\bar z)^2}, \quad
   \mathrm{RMSE} = \sqrt{\tfrac1N\sum (z_i-\hat z_i)^2}, \quad
   \mathrm{Bias} = \tfrac1N\sum(\hat z_i - z_i)

.. math::

   \sigma = \sqrt{\tfrac1N\sum\left[(\hat z_i - z_i) - \mathrm{Bias}\right]^2}, \qquad
   \mathrm{MAE} = \tfrac1N\sum|\hat z_i - z_i|

Difference maps: :math:`\Delta z_B = \hat z_i - z_i` [m] and
:math:`\delta z_B = 100\,(\hat z_i - z_i)/z_i` [%] (only for :math:`z_i > 0.01` m).
Further analyses: parity plots (1:1 line, ±0.5 m and ±1.0 m bands), boxplots of
:math:`|\Delta z_B|` over all 27 versions (box = IQR, whiskers 1.5 × IQR), violin plots of the
selected configurations (y-axis cropped at the 95th percentile) and RMSE/σ in 0.5 m depth bins
with the derivative :math:`\mathrm{d(RMSE)}/\mathrm{d}z` marking the depth of fastest degradation.
