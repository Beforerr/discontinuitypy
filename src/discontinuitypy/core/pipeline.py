# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/00_ids_finder.ipynb.

# %% auto 0
__all__ = ['ids_finder', 'extract_features']

# %% ../../../notebooks/00_ids_finder.ipynb 2
# | code-summary: "Import all the packages needed for the project"
import polars as pl
from ..detection.variance import detect_variance
from .propeties import process_events
from space_analysis.ds.ts.io import df2ts
from loguru import logger

from datetime import timedelta

from typing import Callable

# %% ../../../notebooks/00_ids_finder.ipynb 5
from beforerr.polars import filter_df_by_ranges
def compress_data_by_events(data: pl.DataFrame, events: pl.DataFrame):
    """Compress the data for parallel processing"""
    starts = events["tstart"]
    ends = events["tstop"]
    return filter_df_by_ranges(data, starts, ends)

def get_bcols(df: pl.LazyFrame):
    """Get the magnetic field components"""
    bcols = df.collect_schema().names()
    bcols.remove("time")
    len(bcols) == 3 or logger.error("Expect 3 field components")
    return bcols

# %% ../../../notebooks/00_ids_finder.ipynb 6
def ids_finder(
    detection_df: pl.LazyFrame,  # data used for anomaly dectection (typically low cadence data)
    bcols=None,
    detect_func: Callable[..., pl.LazyFrame] = detect_variance,
    detect_kwargs: dict = {},
    extract_df: pl.LazyFrame = None,  # data used for feature extraction (typically high cadence data),
    **kwargs,
):
    bcols = bcols or get_bcols(detection_df)
    detection_df = detection_df.select(bcols + ["time"]).sort("time")
    extract_df = (extract_df or detection_df).sort("time")

    events = detect_func(detection_df, bcols=bcols, **detect_kwargs)

    data_c = compress_data_by_events(extract_df.collect(), events)
    sat_fgm = df2ts(data_c, bcols)
    ids = process_events(events, sat_fgm, **kwargs)
    return ids

# %% ../../../notebooks/00_ids_finder.ipynb 8
def extract_features(
    partitioned_input: dict[str, Callable[..., pl.LazyFrame]],
    tau: float,  # in seconds, yaml input
    ts: float,  # in seconds, yaml input
    **kwargs,
) -> pl.DataFrame:
    "wrapper function for partitioned input"

    _tau = timedelta(seconds=tau)
    _ts = timedelta(seconds=ts)

    ids = pl.concat(
        [
            ids_finder(partition_load(), _tau, _ts, **kwargs)
            for partition_load in partitioned_input.values()
        ]
    )
    return ids.unique(["d_time", "t.d_start", "t.d_end"])
