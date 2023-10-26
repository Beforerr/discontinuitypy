# Discontinuities? Yes!
Zijin ZhangAnton ArtemyevVassilis AngelopoulosShi ChenZesen Huang

## Install

``` sh
pip install ids-finder
```

## How to use

Import the package

``` python
from ids_finder.utils.basic import *
from ids_finder.core import *
```

## Background

‘Discontinuities’ are discontinuous spatial changes in plasmas
parameters/characteristics and magnetic ﬁelds.

### Importance

- Contribution of Strong Discontinuities to the Power Spectrum

  > The strong discontinuities produce a power-law spectrum in the
  > ‘inertial subrange’ with a spectral index near the Kolmogorov -5/3
  > index. The discontinuity spectrum contains about half of the power
  > of the full solar-wind magnetic ﬁeld over this ‘inertial subrange’.
  > (Borovsky 2010)

### Motivations

Studying the radial distribution of occurrence rate, as well as the
properties of solar wind discontinuities may help answer the following
questions:

- How does the discontinuities change with the radial distance from the
  Sun?
- How is solar wind discontinuities formed? What is the physical
  mechanisms?
  - Generated at or near the sun?
  - Locally generated in the interplanetary space by turbulence?

JUNO mission really provides a unique opportunity!!!

- Five-year cruise to Jupiter from 2011 to 2016
- One earth flyby in 2013
- Nearly the same Heliographic latitude as Earth

To eliminate the effect of the solar wind structure, we use data from
other missions (mainly at 1AU) to provide a way of normalization.

| Mission  | r \[AU\] | $\delta t_B$ | $\delta t_{plasma}$                  | Data availability      |
|----------|----------|--------------|--------------------------------------|------------------------|
| JUNO     | 1-5.5    | 1s           | 1h **model** [\*](#solar-wind-model) | 2011-2016              |
| ARTEMIS  | 1        | 4s           | 1h OMNI                              | 2011-2016 (solar wind) |
| STEREO-A | 1        | 1s           | 1h averaged                          | 2011-2016              |

## Methods

Traditional methods for ID identiﬁcation, such as the criteria of

- Burlaga & Ness (1969; B-criterion) : a directional change of the
  magnetic ﬁeld larger than 30° during 60 s
- Tsurutani & Smith (1979; TS-criterion) : $|ΔB|/|B| \geq 0.5$ within 3
  minutes

Mostly rely on magnetic ﬁeld variations with a certain time lag.
B-criterion has, as its main condition.

In their methods, the IDs below the thresholds are artiﬁcially
abandoned. Therefore, identiﬁcation criteria may affect the statistical
results, and there is likely to be a discrepancy between the ﬁndings via
B-criterion and TS- criterion.

### ID identification (limited feature extraction / anomaly detection)

Liu’s method : The ﬁrst two conditions guar- antee that the ﬁeld changes
of the IDs identiﬁed are large enough to be distinguished from the
stochastic ﬂuctuations on magnetic ﬁelds, while the third is a
supplementary condition to reduce the uncertainty of recognition.

$$ \textrm{Index}_1 = \frac{\sigma(\vec{B})}{Max(\sigma(\vec{B}_-),\sigma(\vec{B}_+))} $$

$$ \textrm{Index}_2 = \frac{\sigma(\vec{B}_- + \vec{B}_+)} {\sigma(\vec{B}_-) + \sigma(\vec{B}_+)} $$

$$ \textrm{Index}_3 = \frac{| \Delta \vec{B} |}{|B_{bg}|} $$

$$ \textrm{Index}_1 \ge 2, \textrm{Index}_2 \ge 1, \textrm{Index}_3 \ge 0.1 $$

### Solar Wind Model

Sadly, JUNO does not provide plasma data during the cruise phase, so to
estimate the plasma state we will use MHD model.

We are using [Michigan Solar WInd Model 2D
(MSWIM2D)](http://csem.engin.umich.edu/MSWIM2D/), which models the solar
wind propagation in 2D using the BATSRUS MHD solver. (Keebler et al.
2022)

Some key points about the model

- Representing the solar wind in the ecliptic plane from 1 to 75 au
- 2D MHD model, using the BATSRUS MHD solver
- Inclusion of neutral hydrogen (important for the outer heliosphere)
- Inner boundary is filled by time-shifting in situ data from multiple
  spacecraft

For model validation part, please see [JUNO Model
Report](./analysis/20_model.ipynb).

## Conventions

As we are dealing with multiple spacecraft, we need to be careful about
naming conventions. Here are the conventions we use in this project.

- `sat_id`: name of the spacecraft. We also use abbreviation, for
  example
  - `sta` for `STEREO-A`
  - `thb` for `ARTEMIS-B`
- `sat_state`: state data of the spacecraft
- `b_vl`: maxium variance vector of the magnetic field, (major
  eigenvector)

### Columns naming conventions

- `radial_distance`: radial distance of the spacecraft, in units of $AU$

- `plasma_speed`: solar wind plasma speed, in units of $km/s$

- `sw_elevation`: solar wind elevation angle, in units of $\degree$

- `sw_azimuth`: solar wind azimuth angle, in units of $\degree$

- `v_{x,y,z}` or `sw_vel_{X,Y,Z}`: solar wind plasma speed in the *ANY*
  coordinate system, in units of $km/s$

  - `sw_vel_{r,t,n}`: solar wind plasma speed in the RTN coordinate
    system, in units of $km/s$
  - `sw_vel_gse_{x,y,z}`: solar wind plasma speed in the GSE coordinate
    system, in units of $km/s$
  - `sw_vel_lmn_{x,y,z}`: solar wind plasma speed in the LMN coordinate
    system, in units of $km/s$
    - `v_l` or `sw_vel_l`: abbreviation for `sw_vel_lmn_1`
    - `v_mn` or `sw_vel_mn` (deprecated)

- `plasma_density`: plasma density, in units of $1/cm^{3}$

- `plasma_temperature`: plasma temperature, in units of $K$

- `b_{x,y,z}`: magnetic field in *ANY* coordinate system

  - `b_rtn_{x,y,z}` or `b_{r,t,n}`: magnetic field in the RTN coordinate
    system
  - `b_gse_{x,y,z}`: magnetic field in the GSE coordinate system

- `b_mag` \| `B_mag`: magnetic field magnitude

- `Vl_{x,y,z}` or `b_vecL_{X,Y,Z}`: maxium variance vector of the
  magnetic field in *ANY* coordinate system

  - `b_vecL_{r,t,n}`: maxium variance vector of the magnetic field in
    the RTN coordinate system

- `model_b_{r,t,n}`: modelled magnetic field in the RTN coordinate
  system

- `state` : *1* for *solar wind*, *0* for *non-solar wind*

- `L_mn{_norm}`: thickness of the current sheet in MN direction, in
  units of $km$

- `j0{_norm}`: current density, in units of $nA/m^2$

Notes: we recommend use unique names for each variable, for example,
`plasma_speed` instead of `speed`. Because it is easier to search and
replace the variable names in the code whenever necessary.

For the dataframe unit, we use

- length : $km$
- time : $s$
- magnetic field : $nT$
- current : $A/m^2$

## Optimizations

``` python
%%markdown
python -X importtime -c 'from ids_finder.pipelines.juno.pipeline import download_juno_data, preprocess_jno' 2> import.log && tuna import.log

python -X importtime -c 'import ids_finder.utils.basic' 2> import.log && tuna import.log
```

## TODOs

Science part

- Analysis
  - [x] Check `STEREO-A` and `ARTEMIS-B` data
  - [ ] Check Datagap
  - [ ] Check `ARTEMIS-B` data in different states (solar wind,
    magnetosheath, magnetotail, moon wake)
  - [ ] Distribution of \|B\| over radius
- Identifaction
  - [ ] Ensemble forest?
  - [ ] Smoothing is important?
  - [ ] Check change point algorithm
- Visualize data gaps
- Features
  - [ ] investigate `d_star` too large
  - [ ] Thickness in N direction
- Compare with other methods of identifying IDs
  - [ ] Verify with other methods of identifying IDs
- [x] Incorporate solar wind propagation model
  - [x] Verify with solar wind propagation model
    - [x] Coordinate transformation

Code part

- Optimization
  - [ ] `JAX` library for `numpy` optimization
- Refactor
  - [x] `process_candidates` to exclude `sat_state` logics
  - [x] renaming feature layer `candidates`
- [x] Kedro
  - [x] Modular pipelines
  - ~~Incorporate `lineapy`~~

### bugs

- [ ] juno `sw_temperature` type
- [ ] STEREO `B` less than zero (after downsampling?)

<div id="refs" class="references csl-bib-body hanging-indent">

<div id="ref-borovsky2010" class="csl-entry">

Borovsky, Joseph E. 2010. “Contribution of Strong Discontinuities to the
Power Spectrum of the Solar Wind.” *Physical Review Letters* 105 (11):
111102. <https://doi.org/10.1103/PhysRevLett.105.111102>.

</div>

<div id="ref-keebler2022" class="csl-entry">

Keebler, Timothy B., Gábor Tóth, Bertalan Zieger, and Merav Opher. 2022.
“MSWIM2D: Two-Dimensional Outer Heliosphere Solar Wind Modeling.” *The
Astrophysical Journal Supplement Series* 260 (2): 43.
<https://doi.org/10.3847/1538-4365/ac67eb>.

</div>

</div>
