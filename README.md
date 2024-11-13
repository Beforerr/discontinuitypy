# DiscontinuityPy


[![PyPI](https://img.shields.io/pypi/v/discontinuitypy.png)](https://pypi.org/project/discontinuitypy)
[![Pixi
Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet.png)](https://pdm-project.org)

# User Guide

This package is designed to identify and analyze discontinuities in time
series data.

1.  Finding the discontinuities, see [this
    notebook](./01_ids_detection.ipynb)
    - Corresponding to limited feature extraction / anomaly detection
2.  Calculating the properties of the discontinuities, see [this
    notebook](./02_ids_properties.ipynb)
    - One can use higher time resolution data

For how to use this project as a python library, please see [this
page](./00_ids_finder.ipynb).

See accompanying package
[Discontinuity.jl](https://beforerr.github.io/Discontinuity.jl) for
Julia about data processing and visualization.

## Installation

``` shell
pip install discontinuitypy
```

## Getting started

Import the package

``` python
from discontinuitypy.utils.basic import *
from discontinuitypy.core import *
```

# Related projects and publications

- [Solar wind discontinuities spatial evolution in the outer
  heliosphere](https://beforerr.github.io/ids_spatial_evolution_juno/)
- [Evolution of solar wind discontinuities in the inner heliosphere: PSP
  and Earth conjunctions and
  alignments](https://beforerr.github.io/psp_conjunction/)

<!-- We have developed a pipeline to identify solar wind discontinuities. (Modular, Performant, Scalable) -->

# Properties of Discontinuities

Notations:

- $\vec{B}$ : Magnetic field in *ANY* coordinate system
- $B$ : Magnetic field magnitude
- $V$ : Ion velocity in *ANY* coordinate system, in units of $km/s$
- $n$ : Plasma density, in units of $1/cm^3$

For the unit, by default we use

- length : $km$
- time : $s$
- magnetic field : $nT$
- current : $nA/m^2$

## Outputs

For more derivable outputs, please see
[Discontinuity.jl](https://beforerr.github.io/Discontinuity.jl)

- `t_{us,ds}` : moments of time corresponding to upstream and downstream
  boundaries of the current sheet

- `b_mag` : mean of magnetic field magnitude across the discontinuity

- $|Δ B|/B$ : Change in magnetic field magnitude over magnetic field
  magnitude (mean) `db_over_b`

  - see Fig.14 in Tsurutani and Smith (1979)

- `bn_over_b` : $\bar{B}_N/\bar{B}$ : Normal component of magnetic field
  over magnetic field magnitude (mean)

- $\vec{e}_l, \vec{e}_m, \vec{e}_n$ : unit vector in the direction of
  the maxium, medium, minium variance magnetic field in *ANY* coordinate
  system `e_{max/med/min}{x,y,z}`

- $\vec{n}$ : normal of the discontinuity plane

- $\vec{n}_{\text{MVA}}$ : normal from minimum variance analysis (unit
  vector in the minium variance direction) `n_mva = e_min`

- $\vec{n}_{\text{cross}}$ : cross product of the magnetic field vector
  $B_u$ upstream and the field vector $B_d$ downstream of the transition
  `n_cross`

- $V$ : Velocity vector in *ANY* coordinate system `V`

- $V_l$ : Velocity component along the maximum variance direction `V_l`

- $V_{n,MVA}$ : Velocity component along the normal direction from
  minimum variance analysis `V_n_mva`

- $V_{n,cross}$ : Velocity component along the normal direction from
  cross product of upstream and downstream magnetic field `V_n_cross`

- `j0{_norm}`: current density, in units of $nA/m^2$

<div id="refs" class="references csl-bib-body hanging-indent"
entry-spacing="0">

<div id="ref-tsurutaniInterplanetaryDiscontinuitiesTemporal1979"
class="csl-entry">

Tsurutani, Bruce T., and Edward J. Smith. 1979. “Interplanetary
Discontinuities: Temporal Variations and the Radial Gradient from 1 to
8.5 AU.” *Journal of Geophysical Research: Space Physics* 84 (A6):
2773–87. <https://doi.org/10.1029/JA084iA06p02773>.

</div>

</div>
