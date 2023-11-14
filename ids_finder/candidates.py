# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/20_candidates.ipynb.

# %% auto 0
__all__ = ['combine', 'vector_project', 'vector_project_pl', 'compute_inertial_length', 'compute_Alfven_speed',
           'compute_Alfven_current', 'calc_combined_features', 'combine_features', 'IDsDataset', 'cIDsDataset',
           'CandidateID']

# %% ../notebooks/20_candidates.ipynb 2
import polars as pl
import polars.selectors as cs
import pandas as pd
import pandas
import xarray as xr

from datetime import timedelta

# %% ../notebooks/20_candidates.ipynb 4
from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline
from .utils.basic import load_catalog

# %% ../notebooks/20_candidates.ipynb 7
import polars as pl

from .utils.basic import df2ts, pl_norm
import xarray as xr
from xarray_einstats import linalg

# %% ../notebooks/20_candidates.ipynb 8
def combine(candidates: pl.LazyFrame, states_data: pl.LazyFrame):
    vec_cols = ["v_x", "v_y", "v_z"]  # plasma velocity vector in any coordinate system
    b_vecL_cols = ["Vl_x", "Vl_y", "Vl_z"]  # major eigenvector in any coordinate system
    if not set(vec_cols).issubset(states_data.columns):
        raise ValueError(f"Missing columns {vec_cols}")
    if not set(b_vecL_cols).issubset(candidates.columns):
        raise ValueError(f"Missing columns {b_vecL_cols}")

    return candidates.sort("time").join_asof(states_data.sort("time"), on="time")

# %% ../notebooks/20_candidates.ipynb 10
import astropy.units as u
from astropy.constants import mu0, e
from plasmapy.formulary.lengths import inertial_length
from plasmapy.formulary.speeds import Alfven_speed

# %% ../notebooks/20_candidates.ipynb 11
def vector_project(v1,v2, dim="v_dim"):
    return xr.dot(v1 , v2, dims=dim) / linalg.norm(v2, dims=dim)

def vector_project_pl(df: pl.DataFrame, v1_cols, v2_cols, name=None):
    
    v1 = df2ts(df, v1_cols).assign_coords(v_dim=["r","t","n"])
    v2 = df2ts(df, v2_cols).assign_coords(v_dim=["r","t","n"]) 
    result = vector_project(v1, v2, dim="v_dim")
    
    return df.with_columns(
        pl.Series(result.data).alias(name or "v_proj")
    )

# %% ../notebooks/20_candidates.ipynb 12
def compute_inertial_length(ldf: pl.LazyFrame):
    df = ldf.collect()

    density = df["plasma_density"].to_numpy() * u.cm ** (-3)
    result = inertial_length(density, "H+").to(u.km)

    return df.with_columns(ion_inertial_length=pl.Series(result.value)).lazy()


def compute_Alfven_speed(ldf: pl.LazyFrame):
    df = ldf.collect()

    B = df["B"] if "B" in df.columns else df["b_mag"]  # backwards compatiblity
    density = df["plasma_density"].to_numpy() * u.cm ** (-3)
    result = Alfven_speed(B.to_numpy() * u.nT, density=density, ion="p+").to(u.km / u.s)

    return df.with_columns(Alfven_speed=pl.Series(result.value)).lazy()


def compute_Alfven_current(ldf: pl.LazyFrame):
    df = ldf.collect()

    Alfven_speed = df["Alfven_speed"].to_numpy() * u.km / u.s
    density = df["plasma_density"].to_numpy() * u.cm ** (-3)

    result = (e.si * Alfven_speed * density)
    result = result.to(u.nA / u.m**2)

    return df.with_columns(j_Alfven=pl.Series(result.value)).lazy()

# %% ../notebooks/20_candidates.ipynb 13
def calc_combined_features(df: pl.LazyFrame):
    vec_cols = ["v_x", "v_y", "v_z"]  # plasma velocity vector in any coordinate system
    b_vecL_cols = ["Vl_x", "Vl_y", "Vl_z"]  # major eigenvector in any coordinate system

    j_factor = ((u.nT / u.s) * (1 / mu0 / (u.km / u.s))).to(u.nA / u.m**2)

    result = (
        df.with_columns(
            duration=pl.col("d_tstop") - pl.col("d_tstart"),
        )
        .pipe(vector_project_pl, vec_cols, b_vecL_cols, name="v_l")
        .with_columns(v_mn=(pl.col("plasma_speed") ** 2 - pl.col("v_l") ** 2).sqrt())
        .with_columns(
            L_mn=pl.col("v_mn") * pl.col("duration").dt.nanoseconds() / 1e9,
            j0=pl.col("d_star") / pl.col("v_mn"),
        )
        .pipe(compute_inertial_length)
        .pipe(compute_Alfven_speed)
        .pipe(compute_Alfven_current)
        .pipe(j0=pl.col("j0") * j_factor.value)
        .with_columns(
            L_mn_norm=pl.col("L_mn") / pl.col("ion_inertial_length"),
            j0_norm=pl.col("j0") / pl.col("j_Alfven"),
        )
    )
    return result

# %% ../notebooks/20_candidates.ipynb 15
def combine_features(candidates: pl.LazyFrame, states_data: pl.LazyFrame):
    df = combine(candidates, states_data)
    updated_df = calc_combined_features(df)

    return updated_df.collect()

# %% ../notebooks/20_candidates.ipynb 17
from pydantic import BaseModel
from kedro.io import DataCatalog
from .utils.basic import concat_partitions

# %% ../notebooks/20_candidates.ipynb 19
from .utils.basic import df2ts
from .utils.plot import plot_candidate

# %% ../notebooks/20_candidates.ipynb 20
class IDsDataset(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    sat_id: str
    tau: timedelta
    ts: timedelta = timedelta(seconds=1)

    candidates: pl.DataFrame | None = None
    data: pl.LazyFrame | None = None # data is large, so we use `pl.LazyFrame` to save memory

    def plot_candidate(self, index = None, predicates = None):
        if index is not None:
            candidate = self.candidates.row(index, named=True)
        elif predicates is not None:
            candidate = self.candidates.filter(predicates).row(0, named=True)

        _data = self.data.filter(
            pl.col("time").is_between(candidate["tstart"], candidate["tstop"])
        )
        bcols = ["B_x", "B_y", "B_z"] if "B_x" in _data.columns else ["BX", "BY", "BZ"]
        sat_fgm = df2ts(_data, bcols)
        plot_candidate(candidate, sat_fgm)
        pass

    def plot_candidates(self, **kwargs):
        pass

# %% ../notebooks/20_candidates.ipynb 22
class cIDsDataset(IDsDataset):
    catalog: DataCatalog
    
    or_df: pl.DataFrame | None = None  # occurence rate
    or_df_normalized: pl.DataFrame | None = None # normalized occurence rate

    def __init__(self, **data):
        super().__init__(**data)
        
        self._tau_str = f"tau_{self.tau.seconds}s"
        self._ts_mag_str = f"ts_{self.ts.seconds}s"
        
        if self.candidates is None:
            self.load_candidates()
        if self.data is None:
            self.load_data()

    def load_candidates(self):

        candidates_format = f"candidates.{self.sat_id}_{self._ts_mag_str}_{self._tau_str}"

        self.candidates = self.catalog.load(candidates_format).fill_nan(None).with_columns(
            cs.float().cast(pl.Float64),
            sat=pl.lit(self.sat_id),
        ).collect()

    def load_data(self):
        data_format = f"{self.sat_id}.primary_mag_{self._ts_mag_str}"
        self.data = concat_partitions(self.catalog.load(data_format))

# %% ../notebooks/20_candidates.ipynb 24
from pprint import pprint

# %% ../notebooks/20_candidates.ipynb 25
class CandidateID:
    def __init__(self, time, df: pl.DataFrame) -> None:
        self.time = pd.Timestamp(time)
        self.data = df.row(
            by_predicate=(pl.col("time") == self.time), 
            named=True
        )

    def __repr__(self) -> str:
        # return self.data.__repr__()
        pprint(self.data)
        return ''
    
    def plot(self, sat_fgm, tau):
        plot_candidate_xr(self.data, sat_fgm, tau)
        pass
        
