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

# TODOs

Science part

- Analysis
  - [ ] Contribution of discontinuities to the power spectrum
  - [ ] Check Datagap
  - [ ] Distribution of \|B\| over radius
  - [ ] Add error bar
  - [ ] More accurate way to obtain the properties of the
    discontinuities
- Identifaction
  - [ ] Ensemble forest?
  - [ ] Smoothing is important?
  - [ ] Check change point algorithm
- Features
  - [ ] Thickness in N direction
  - [ ] Use high resolution data for feature extraction
- Compare with other methods of identifying IDs
  - [ ] Verify with other methods of identifying IDs

Code part

- Optimization
  - [ ] `dask` for parallel computing instead of `modin`
  - [ ] `JAX` library for `numpy` optimization
  - [ ] shorten import time
- Refactor
  - [x] `process_candidates` to exclude `sat_state` logics
  - [x] renaming feature layer `candidates`
- [x] Kedro
  - [x] Modular pipelines

### bugs

- [ ] STEREO `B` less than zero (after downsampling?)
