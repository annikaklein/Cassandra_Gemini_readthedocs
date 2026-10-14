Results
=======

Overview
--------

The framework is evaluated within a **0–10 m** depth range, the range over which the
underlying radiative transfer formulation (Albert 2004) performs reliably. The retrieved depth
:math:`z_B` is the total water column depth at the moment of acquisition and therefore includes
tidal stage (One Tree Reef) or gauge-level variations (Lake Constance); a tidal or gauge
correction is applied separately to reach a common vertical datum.

The four-stage pipeline (preprocessing → initial estimates → per-band inversion → export) is
shown in :doc:`methods`.

Site Comparison
---------------

The 27 configurations (:doc:`methods`) were evaluated at both sites: Lake Constance (Secchi 6–9 m,
meso-oligotrophic) and One Tree Reef (Secchi ≈ 15 m, oligotrophic).

.. todo:: Add Figure *boxplots_combined* (absolute error distribution of all 27 versions;
   orange = Lake Constance, blue = One Tree Reef; box = IQR, whiskers 1.5 × IQR; N printed next to each box).

**Error levels.** Lake Constance gives low, compact distributions (medians ≈ 0.15–0.40 m,
IQR < 0.30 m, whiskers ≤ 0.75 m for V1–9 and V19–27 and up to 1.2 m for V10–18). One Tree Reef
shows medians of ≈ 0.40–0.60 m, much wider boxes and whiskers up to 2.5 m, and a stronger
sensitivity to the parameterisation.

**Convergence criterion.** Configurations with notably low pixel counts N are disqualified
regardless of their median error. At Lake Constance this affects V4 (N = 8390) and V22
(N = 8198); at One Tree Reef V8 (N = 9574), V26 (N = 9357) and V27 (N = 9788) show reduced
convergence.

**Best configuration.** After this criterion, **Version 6** (C\ :sub:`X,A`, C\ :sub:`P,E1`,
a\ :sub:`Y,E2`) is the best configuration across both environments and is referred to as
*Cassandra Gemini*.

**Controls on accuracy.**

- *TSM* is the dominant control: versions sharing a TSM pathway cluster (V1–9: A, V10–18: E1,
  V19–27: E2); V10–18 have about twice the median error of V1–9 at Lake Constance.
- *Chl-a* is second order (V5–6, CP E1, give slightly more compact distributions at One Tree Reef).
- *CDOM* plays a minor role (V1–3 differ only in CDOM and are virtually indistinguishable).
- A hybrid setup — semi-analytical TSM with empirical Chl-a and CDOM — outperforms all-analytical
  and all-empirical configurations; whether this generalises beyond the two sites remains open.

.. todo:: Add Figure *violin_figure_depth_errors_95* (V1 vs. V6 at both sites).

**Version 1 (Albert-based) vs. Version 6.** At Lake Constance both reach a median of 0.18 m and
0.20 m and RMSE = 0.38 m. At One Tree Reef the median decreases from 0.52 m to 0.43 m and RMSE
from 0.92 m to 0.79 m, but *Cassandra Gemini* converges on about 2.8 % fewer pixels, so part
of the improvement may be a selection effect.

.. todo:: Add Figure *rmse_derivative_selected_versions* (RMSE versus depth and its derivative).

**Depth dependence.** RMSE grows with depth at both sites. The derivative of the RMSE with
respect to depth peaks at **3.50–3.93 m at Lake Constance** and **4.92–6.38 m at One Tree Reef**,
consistent with the penetration depth of the red band (Landsat 8 SR_B4, 655 nm), which
attenuates faster in the turbid lake (Xu et al., 2021; Kalybekova 2025). Beyond this depth the
bottom signal can no longer be separated from the water column signal.

Validation
----------

The pixel-wise comparison with LiDAR reference bathymetry (0–10 m) is summarised in six panels
per site: reference depth, estimated depth, relative difference
:math:`\delta z_B`, signed difference :math:`\Delta z_B`, absolute difference
:math:`|\Delta z_B|` and a parity plot.

.. list-table::
   :header-rows: 1

   * - Site
     - N
     - R²
     - RMSE
     - MAE
     - Bias
     - Range of Δz\ :sub:`B`
   * - Lake Constance
     - 15 754
     - 0.68
     - 0.38 m
     - 0.24 m
     - −0.03 m
     - −5.60 to +1.64 m
   * - One Tree Reef
     - 13 192
     - 0.54
     - 0.79 m
     - 0.58 m
     - −0.05 m
     - −5.49 to +4.41 m

**Lake Constance.** The shallow platform is reproduced in extent and gradient; δz\ :sub:`B`
ranges from −86.1 % to +82.4 %, mostly within ±50 %, with a slight overestimation tendency.
Isolated large errors (≈ 5.6 m) sit at the deepest margins (beyond the red-band penetration
depth). Wave breaking and residual land–water pixels at the Horn shoreline may contribute.

**One Tree Reef.** δz\ :sub:`B` ranges from −83.1 % to +1109 % (colour scale clipped at ±100 %);
extreme values occur where the reference depth is very small. Depth is overestimated at the outer
reef rim and around the island and channel networks (sub-pixel structure at 30 m resolution,
mixed pixels, wave breaking) and slightly underestimated in the inner reef.

.. todo:: Add Figures *LC_fig_combined_6panel* and *OTR_fig_combined_6panel*.

EOMAP Comparison
----------------

*Cassandra Gemini* is compared with the commercial EOMAP WATCOR-X product (multi-temporal
Sentinel-2, 10 m) at One Tree Reef, using the same LiDAR reference and only the pixels covered by
both products.

.. list-table::
   :header-rows: 1

   * - Product
     - R²
     - RMSE
     - MAE
     - Bias
   * - EOMAP WATCOR-X
     - −0.09
     - 1.20 m
     - 0.72 m
     - −0.56 m
   * - Cassandra Gemini
     - 0.54
     - 0.79 m
     - 0.58 m
     - ≈ 0.05 m (magnitude; see note)

RMSE is reduced by ≈ 34 % relative to EOMAP. Caveats: (1) EOMAP extends well beyond the 10 m
limit of this framework, so only a subset of its capability is evaluated; (2) the 10 m Sentinel-2
resolution resolves reef structures that are smoothed at 30 m. The advantage therefore holds for
the jointly accessible depth range and spatial scale only.

.. todo:: Add Figure *OTI_parity_EOMAP_vs_LiDAR__Cassandra_vs_LiDAR* (parity plots).

.. note:: The sign of the bias of *Cassandra Gemini* differs between the text sections of the
   manuscript (−0.05 m in Validation, +0.05 m in the EOMAP comparison); please unify.
