## TODOs

Science part

-   Analysis
    -   [ ] Contribution of discontinuities to the power spectrum
    -   [ ] Check Datagap
    -   [ ] Distribution of \|B\| over radius
    -   [ ] Add error bar
    -   [ ] More accurate way to obtain the properties of the discontinuities
-   Identifaction
    -   [ ] Ensemble forest?
    -   [ ] Smoothing is important?
    -   [ ] Check change point algorithm
-   Features
    -   [ ] Thickness in N direction
    -   [ ] Use high resolution data for feature extraction
-   Compare with other methods of identifying IDs
    -   [ ] Verify with other methods of identifying IDs

Code part

-   Optimization
    -   [ ] `dask` for parallel computing instead of `modin`
    -   [ ] `JAX` library for `numpy` optimization
    -   [ ] shorten import time
-   Refactor
    -   [x] `process_candidates` to exclude `sat_state` logics
    -   [x] renaming feature layer `candidates`
-   [x] Kedro
    -   [x] Modular pipelines