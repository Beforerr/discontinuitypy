# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/properties/00_duration.ipynb.

# %% auto 0
__all__ = ['THRESHOLD_RATIO', 'AvailableMethod', 'ts_max_distance', 'ts_max_derivative', 'find_start_end_times',
           'get_time_from_condition', 'calc_duration']

# %% ../../../notebooks/properties/00_duration.ipynb 1
from scipy.spatial import distance_matrix
import xarray as xr
import numpy as np
import pandas as pd
from xarray_einstats import linalg
from typing import Literal

# %% ../../../notebooks/properties/00_duration.ipynb 3
def ts_max_distance(ts: xr.DataArray, coord: str = "time"):
    "Compute the time interval when the timeseries has maxium cumulative variation"
    distance = distance_matrix(ts.data, ts.data)
    max_distance_index = np.unravel_index(np.argmax(distance), distance.shape)
    return ts[coord].values[list(max_distance_index)]

# %% ../../../notebooks/properties/00_duration.ipynb 6
THRESHOLD_RATIO = 1 / 4


def ts_max_derivative(vec: xr.DataArray, threshold_ratio=THRESHOLD_RATIO):
    # NOTE: gradient calculated at the edge is not reliable.
    vec_diff = vec.differentiate("time", datetime_unit="s").isel(time=slice(1, -1))
    vec_diff_mag = linalg.norm(vec_diff, dims="v_dim")

    # Determine d_star based on trend
    if vec_diff_mag.isnull().all():
        raise ValueError(
            "The differentiated vector magnitude contains only NaN values. Cannot compute duration."
        )

    d_star_index = vec_diff_mag.argmax(dim="time")
    d_star = vec_diff_mag[d_star_index].item()
    d_time = vec_diff_mag.time[d_star_index].values

    threshold = d_star * threshold_ratio

    start_time, end_time = find_start_end_times(vec_diff_mag, d_time, threshold)

    return start_time, end_time, d_time, d_star


def find_start_end_times(
    vec_diff_mag: xr.DataArray, d_time, threshold
) -> tuple[pd.Timestamp, pd.Timestamp]:
    # Determine start time
    pre_vec_mag = vec_diff_mag.sel(time=slice(None, d_time))
    start_time = get_time_from_condition(pre_vec_mag, threshold, "last_below")

    # Determine stop time
    post_vec_mag = vec_diff_mag.sel(time=slice(d_time, None))
    end_time = get_time_from_condition(post_vec_mag, threshold, "first_below")

    return start_time, end_time


def get_time_from_condition(
    vec: xr.DataArray, threshold, condition_type
) -> pd.Timestamp:
    if condition_type == "first_below":
        condition = vec < threshold
        index_choice = 0
    elif condition_type == "last_below":
        condition = vec < threshold
        index_choice = -1
    else:
        raise ValueError(f"Unknown condition_type: {condition_type}")

    where_result = np.where(condition)[0]

    if len(where_result) > 0:
        return vec.time[where_result[index_choice]].values
    return None

# %% ../../../notebooks/properties/00_duration.ipynb 7
AvailableMethod = Literal["distance", "derivative"]


def calc_duration(ts: xr.DataArray, method: AvailableMethod = "distance", **kwargs):
    if method == "distance":
        result = np.sort(ts_max_distance(ts))
        keys = ["t_us", "t_ds"]

    elif method == "derivative":
        result = ts_max_derivative(ts)
        keys = ["t_us", "t_ds", "t.d_time", "d_star_max"]

    return dict(zip(keys, result))
