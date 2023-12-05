# Discontinuities? Yes!
Zijin ZhangAnton ArtemyevVassilis AngelopoulosShi Chen

For how to use this project as a python library, please see [this
page](./00_ids_finder.ipynb).

- [AGU23 Poster](./manuscripts/AGU23_poster.qmd)
- [Paper](./manuscripts/paper.qmd)

## TODOs

Science part

- Analysis
  - [x] Check `STEREO-A` and `ARTEMIS-B` data
  - [ ] Contribution of discontinuities to the power spectrum
  - [ ] Check Datagap
  - [ ] Check `ARTEMIS-B` data in different states (solar wind,
    magnetosheath, magnetotail, moon wake)
  - [ ] Distribution of \|B\| over radius
  - [ ] JUNO from 2012-09~2012-10 lack of IDS and extreme large
    thickness
  - [ ] Wind data
  - [ ] Add error bar
  - [ ] Validate the effects of calibrate candidate duration
  - [ ] Validate model density with `Voyager`
- Identifaction
  - [ ] Ensemble forest?
  - [ ] Smoothing is important?
  - [ ] Check change point algorithm
- Visualize data gaps
- Features
  - [ ] Thickness in N direction
  - [ ] Use high resolution data for feature extraction
- Compare with other methods of identifying IDs
  - [ ] Verify with other methods of identifying IDs
- [x] Incorporate solar wind propagation model
  - [x] Verify with solar wind propagation model
    - [x] Coordinate transformation

Code part

- Optimization
  - [ ] `JAX` library for `numpy` optimization
  - [ ] shorten import time
- Refactor
  - [x] `process_candidates` to exclude `sat_state` logics
  - [x] renaming feature layer `candidates`
- [x] Kedro
  - [x] Modular pipelines
  - ~~Incorporate `lineapy`~~
- [x] QR codes

### bugs

- [x] JUNO sw_temperature type
- [ ] STEREO `B` less than zero (after downsampling?)
