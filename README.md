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

- $\vec{B}$ : Magnetic field
- $B$ : Magnetic field magnitude

## Outputs

- `b_mag` : mean of magnetic field magnitude across the discontinuity
- `db_over_b` : $|\Delta B|/\bar{B}$ , Change in magnetic field
  magnitude over magnetic field magnitude (mean)
  - see Fig.14 in Tsurutani and Smith (1979)
- `rotation_angle` : Rotation angle across the discontinuity
  - see Fig.12 in Tsurutani and Smith (1979)
  - see Fig.11 in Söding et al. (2001)
- `bn_over_b` : $\bar{B}_N/\bar{B}$ : Normal component of magnetic field
  over magnetic field magnitude (mean)

<div id="refs" class="references csl-bib-body hanging-indent"
entry-spacing="0">

<div id="ref-sodingRadialLatitudinalDependencies2001" class="csl-entry">

Söding, A., F. M. Neubauer, B. T. Tsurutani, N. F. Ness, and R. P.
Lepping. 2001. “Radial and Latitudinal Dependencies of Discontinuities
in the Solar Wind Between 0.3 and 19 AU and -80$^\circ$ and
+10$^\circ$.” *Annales Geophysicae* 19 (7): 667–80.
<https://doi.org/10.5194/angeo-19-667-2001>.

</div>

<div id="ref-tsurutaniInterplanetaryDiscontinuitiesTemporal1979"
class="csl-entry">

Tsurutani, Bruce T., and Edward J. Smith. 1979. “Interplanetary
Discontinuities: Temporal Variations and the Radial Gradient from 1 to
8.5 AU.” *Journal of Geophysical Research: Space Physics* 84 (A6):
2773–87. <https://doi.org/10.1029/JA084iA06p02773>.

</div>

</div>
