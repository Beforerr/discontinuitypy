# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/20_datasets.ipynb.

# %% auto 0
__all__ = ['IDsDataset', 'cIDsDataset', 'CandidateID']

# %% ../notebooks/20_datasets.ipynb 2
import polars as pl
import polars.selectors as cs
import pandas as pd
import pandas
import xarray as xr

from datetime import timedelta

# %% ../notebooks/20_datasets.ipynb 4
from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline
from .utils.basic import load_catalog

# %% ../notebooks/20_datasets.ipynb 6
from pydantic import BaseModel
from kedro.io import DataCatalog
from .utils.basic import concat_partitions

# %% ../notebooks/20_datasets.ipynb 8
from .utils.basic import df2ts
from .utils.plot import plot_candidate

# %% ../notebooks/20_datasets.ipynb 9
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

# %% ../notebooks/20_datasets.ipynb 11
class cIDsDataset(IDsDataset):
    catalog: DataCatalog

    _load_data_format = "{sat}.MAG.primary_data_{ts}"
    _load_events_format = "events.{sat}_{ts}_{tau}"
    or_df: pl.DataFrame | None = None  # occurence rate
    or_df_normalized: pl.DataFrame | None = None  # normalized occurence rate

    def __init__(self, **data):
        super().__init__(**data)

        tau_str = f"tau_{self.tau.seconds}s"
        ts_mag_str = f"ts_{self.ts.seconds}s"

        self._tau_str = tau_str
        self._ts_mag_str = ts_mag_str

        self.events_format = self._load_events_format.format(
            sat=self.sat_id, ts=ts_mag_str, tau=tau_str
        )

        if data.get("data_format") is None:
            self.data_format = self._load_data_format.format(
                sat=self.sat_id, ts=ts_mag_str
            )

        if self.candidates is None:
            self.load_events()
        if self.data is None:
            self.load_data()

    def load_events(self):
        data_format = self.events_format
        self.candidates = (
            self.catalog.load(data_format)
            .fill_nan(None)
            .with_columns(
                cs.float().cast(pl.Float64),
                sat=pl.lit(self.sat_id),
            )
            .collect()
        )

    def load_data(self):
        data_format = self.data_format
        self.data = concat_partitions(self.catalog.load(data_format))

# %% ../notebooks/20_datasets.ipynb 13
from pprint import pprint

# %% ../notebooks/20_datasets.ipynb 14
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
        
