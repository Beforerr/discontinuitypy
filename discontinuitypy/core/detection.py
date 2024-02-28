# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/01_ids_detection.ipynb.

# %% auto 0
__all__ = ['pl_format_time', 'detect_events']

# %% ../../notebooks/01_ids_detection.ipynb 1
from datetime import timedelta
import polars as pl

from typing import overload

# %% ../../notebooks/01_ids_detection.ipynb 2
# some helper functions
@overload
def pl_format_time(df: pl.DataFrame, tau: timedelta) -> pl.DataFrame: pass

@overload
def pl_format_time(df: pl.LazyFrame, tau: timedelta) -> pl.LazyFrame: pass

def pl_format_time(df: pl.LazyFrame, tau: timedelta):
    return df.with_columns(
        tstart=pl.col("time"),
        tstop=(pl.col("time") + tau),
        time=(pl.col("time") + tau / 2),
    )

# %% ../../notebooks/01_ids_detection.ipynb 4
from ..detection.variance import compute_indices, filter_indices

def detect_events(
    data: pl.LazyFrame,
    tau: timedelta,
    ts: timedelta,
    bcols,
    sparse_num=None,
    method="liu",
    **kwargs,
):
    indices = compute_indices(data, tau, bcols)
    if sparse_num is None:
        sparse_num = tau / ts // 3

    events = indices.pipe(filter_indices, sparse_num=sparse_num).pipe(
        pl_format_time, tau
    ).collect()

    return events
