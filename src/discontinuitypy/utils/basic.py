# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/utils/00_basic.ipynb.

# %% auto 0
__all__ = ['DF_TYPE', 'filter_tranges', 'filter_tranges_df', 'partition_data_by_ts', 'partition_data_by_year',
           'partition_data_by_year_month', 'partition_data_by_time', 'concat_df', 'concat_partitions',
           'format_timedelta', 'resample', 'calc_vec_mag', 'check_fgm']

# %% ../../../notebooks/utils/00_basic.ipynb 1
from typing import overload
from typing import Union, Collection, Callable, Tuple
from typing import Any, Dict

# %% ../../../notebooks/utils/00_basic.ipynb 2
import polars as pl
import polars.selectors as cs

import pandas as pd
import xarray as xr

import pandas
import numpy as np
from xarray_einstats import linalg

from datetime import timedelta

from loguru import logger

from xarray import DataArray
from space_analysis.ds.ts.io import df2ts as df2ts

# %% ../../../notebooks/utils/00_basic.ipynb 4
from fastcore.utils import patch

# %% ../../../notebooks/utils/00_basic.ipynb 5
def filter_tranges(time: pl.Series, tranges: Tuple[list, list]):
    """
    - Filter data by time ranges, return the indices of the time that are in the time ranges (left inclusive, right exclusive)
    """

    starts = tranges[0]
    ends = tranges[1]

    start_indices = time.search_sorted(starts)
    end_indices = time.search_sorted(ends)

    return np.concatenate(
        [
            np.arange(start_index, end_index)
            for start_index, end_index in zip(start_indices, end_indices)
        ]
    )


def filter_tranges_df(
    df: pl.DataFrame, tranges: Tuple[list, list], time_col: str = "time"
):
    """
    - Filter data by time ranges
    """

    time = df[time_col]
    filtered_indices = filter_tranges(time, tranges)
    return df[filtered_indices]

# %% ../../../notebooks/utils/00_basic.ipynb 6
@patch
def plot(self: pl.DataFrame, *args, **kwargs):
    return self.to_pandas().plot(*args, **kwargs)

# %% ../../../notebooks/utils/00_basic.ipynb 7
def _expand_selectors(items: Any, *more_items: Any) -> list[Any]:
    """
    See `_expand_selectors` in `polars`.
    """
    expanded: list[Any] = []
    for item in (
        *(
            items
            if isinstance(items, Collection) and not isinstance(items, str)
            else [items]
        ),
        *more_items,
    ):
        expanded.append(item)
    return expanded

# %% ../../../notebooks/utils/00_basic.ipynb 9
def partition_data_by_ts(df: pl.DataFrame, ts: timedelta) -> Dict[str, pl.DataFrame]:
    """Partition the dataset by time

    Args:
        df: Input DataFrame.
        ts: Time interval.

    Returns:
        Partitioned DataFrame.
    """
    return df.with_columns(
        key=pl.col("time").dt.truncate(ts).cast(pl.Utf8)
    ).partition_by("key", include_key=False, as_dict=True)


def partition_data_by_year(df: pl.DataFrame) -> Dict[str, pl.DataFrame]:
    """Partition the dataset by year

    Args:
        df: Input DataFrame.

    Returns:
        Partitioned DataFrame.
    """
    return df.with_columns(year=pl.col("time").dt.year().cast(pl.Utf8)).partition_by(
        "year", include_key=False, as_dict=True
    )


def partition_data_by_year_month(df: pl.DataFrame) -> Dict[str, pl.DataFrame]:
    """Partition the dataset by year

    Args:
        df: Input DataFrame.

    Returns:
        Partitioned DataFrame.
    """
    return df.with_columns(
        year_month=pl.col("time").dt.year().cast(pl.Utf8)
        + "_"
        + pl.col("time").dt.month().cast(pl.Utf8).str.zfill(2),
    ).partition_by("year_month", include_key=False, as_dict=True)


def partition_data_by_time(
    df: pl.LazyFrame | pl.DataFrame, method
) -> Dict[str, pl.DataFrame]:
    """Partition the dataset by time

    Args:
        df: Input DataFrame.
        method: The method to partition the data.

    Returns:
        Partitioned DataFrame.
    """
    if isinstance(df, pl.LazyFrame):
        df = df.collect()

    if method == "year":
        return partition_data_by_year(df)
    elif method == "year_month":
        return partition_data_by_year_month(df)
    else:
        ts = pd.Timedelta(method)
        return partition_data_by_ts(df, ts)

# %% ../../../notebooks/utils/00_basic.ipynb 10
DF_TYPE = Union[pl.DataFrame, pl.LazyFrame, pd.DataFrame]


def concat_df(dfs: list[DF_TYPE]) -> DF_TYPE:
    """Concatenate a list of DataFrames into one DataFrame."""

    match type(dfs[0]):
        case pl.DataFrame | pl.LazyFrame:
            concat_func = pl.concat
        case pandas.DataFrame:
            concat_func = pandas.concat
        case _:
            raise ValueError(f"Unsupported DataFrame type: {type(dfs[0])}")

    return concat_func(dfs)


def concat_partitions(partitioned_input: Dict[str, Callable]):
    """Concatenate input partitions into one DataFrame.

    Args:
        partitioned_input: A dictionary with partition ids as keys and load functions as values.
    """
    partitions_data = [
        partition_load_func() for partition_load_func in partitioned_input.values()
    ]  # load the actual partition data

    result = concat_df(partitions_data)
    return result

# %% ../../../notebooks/utils/00_basic.ipynb 12
def format_timedelta(time):
    """Format timedelta to `timedelta`"""
    if isinstance(time, timedelta):
        return time
    elif isinstance(time, str):
        return pd.Timedelta(time)
    elif isinstance(time, int):
        return pd.Timedelta(seconds=time)
    else:
        raise TypeError(f"Unsupported type: {type(time)}")

# %% ../../../notebooks/utils/00_basic.ipynb 13
@overload
def resample(
    df: pl.DataFrame,
    every: timedelta,
    period: timedelta = None,
    offset: timedelta = None,
    shift: timedelta = None,
    time_column="time",
) -> pl.DataFrame: ...


@overload
def resample(
    df: pl.LazyFrame,
    every: timedelta,
    period: timedelta = None,
    offset: timedelta = None,
    shift: timedelta = None,
    time_column="time",
) -> pl.LazyFrame: ...


def resample(
    df: pl.LazyFrame | pl.DataFrame,
    every: timedelta,
    period: timedelta = None,
    offset: timedelta = None,
    shift: timedelta = None,
    time_column="time",
):
    """Resample the DataFrame"""
    if period is None:
        period = every
    if shift is None:
        shift = period / 2
    return (
        df.sort(time_column)
        .group_by_dynamic(time_column, every=every, period=period, offset=offset)
        .agg(cs.numeric().mean())
        .with_columns((pl.col(time_column) + shift))
    )

# %% ../../../notebooks/utils/00_basic.ipynb 14
def calc_vec_mag(vec) -> DataArray:
    return linalg.norm(vec, dims="v_dim")

# %% ../../../notebooks/utils/00_basic.ipynb 15
def check_fgm(vec: xr.DataArray):
    # check if time is monotonic increasing
    logger.info("Check if time is monotonic increasing")
    assert vec.time.to_series().is_monotonic_increasing
    # check available time difference
    logger.info(
        f"Available time delta: {vec.time.diff(dim='time').to_series().unique()}"
    )
