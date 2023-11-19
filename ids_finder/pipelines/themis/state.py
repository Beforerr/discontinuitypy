# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/themis/state.ipynb.

# %% auto 0
__all__ = ['omni_yaml', 'OMNI_VARS', 'check_dataype', 'download_state_data', 'load_data', 'preprocess_data', 'flow2gse',
           'filter_tranges', 'process_data', 'load_sw_data', 'preprocess_sw_data', 'create_sw_pipeline',
           'create_pipeline']

# %% ../../../notebooks/missions/themis/state.ipynb 2
from datetime import timedelta

import polars as pl
import pandas
import numpy as np

from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline
from ..default.data import create_pipeline_template

# %% ../../../notebooks/missions/themis/state.ipynb 5
import yaml

omni_yaml = """
  "N":
    COLNAME: "plasma_density"
    FIELDNAM: "Ion density"
    UNITS: "Per cc"
  "T":
    COLNAME: "plasma_temperature"
    FIELDNAM: "Plasma temperature"
    UNITS: "K"
  "V":
    COLNAME: "plasma_speed"
    FIELDNAM: "Flow speed"
    UNITS: "km/s"
  "THETA-V":
    COLNAME: "sw_vel_theta"
    FIELDNAM: "Flow latitude"
    UNITS: "Deg"
  "PHI-V":
    COLNAME: "sw_vel_phi"
    FIELDNAM: "Flow longitude"
    UNITS: "Deg"
"""
OMNI_VARS = yaml.safe_load(omni_yaml)

# %% ../../../notebooks/missions/themis/state.ipynb 6
from ...utils.basic import cdf2pl, pmap

# %% ../../../notebooks/missions/themis/state.ipynb 7
def check_dataype(ts):
    if ts >= 60 * 60:
        return "hourly"
    else:
        return "1min"

# %% ../../../notebooks/missions/themis/state.ipynb 8
def download_state_data(
    start,
    end,
    datatype,
):
    import pyspedas

    trange = [start, end]
    files = pyspedas.omni.data(trange=trange, datatype=datatype, downloadonly=True)
    return files


def load_data(
    start,
    end,
    datatype="hourly",
    vars: dict = OMNI_VARS,
) -> pl.LazyFrame:
    files = download_state_data(start, end, datatype=datatype)
    df: pl.LazyFrame = pl.concat(files | pmap(cdf2pl, var_names=list(vars)))
    return df

# %% ../../../notebooks/missions/themis/state.ipynb 10
def preprocess_data(
    raw_data: pl.LazyFrame,
    vars: dict = OMNI_VARS,
) -> pl.LazyFrame:
    """
    Preprocess the raw dataset (only minor transformations)

    - Applying naming conventions for columns
    - Extracting variables from `CDF` files, and convert them to DataFrame
    """

    columns_name_mapping = {key: value["COLNAME"] for key, value in vars.items()}

    return raw_data.rename(columns_name_mapping)

# %% ../../../notebooks/missions/themis/state.ipynb 12
def flow2gse(df: pl.LazyFrame) -> pl.LazyFrame:
    """
    - Transforming solar wind data from `Quasi-GSE` coordinate to GSE coordinate system
    """
    plasma_speed = pl.col("plasma_speed")
    sw_theta = pl.col("sw_vel_theta")
    sw_phi = pl.col("sw_vel_phi")

    return df.with_columns(
        sw_vel_gse_x=-plasma_speed * sw_theta.cos() * sw_phi.cos(),
        sw_vel_gse_y=+plasma_speed * sw_theta.cos() * sw_phi.sin(),
        sw_vel_gse_z=+plasma_speed * sw_theta.sin(),
    ).drop(["sw_theta", "sw_phi"])


def filter_tranges(time: pl.Series, tranges: tuple[list, list]):
    """
    - Filter data by time ranges, return the indices of the time that are in the time ranges
    """

    starts = tranges[0]
    ends = tranges[1]

    start_indices = time.search_sorted(starts)
    end_indices = time.search_sorted(ends)

    return np.concatenate(
        [
            np.arange(start_index, end_index + 1)
            for start_index, end_index in zip(start_indices, end_indices)
        ]
    )


def process_data(
    raw_data: pl.LazyFrame,
    ts=None,  # time resolution
) -> pl.LazyFrame:
    """
    - Transforming data to GSE coordinate system
    """

    return raw_data.pipe(flow2gse).rename(
        {
            "sw_vel_gse_x": "v_x",
            "sw_vel_gse_y": "v_y",
            "sw_vel_gse_z": "v_z",
        }
    )

# %% ../../../notebooks/missions/themis/state.ipynb 14
def load_sw_data(raw_data: pandas.DataFrame):
    return pl.from_dataframe(raw_data)

# %% ../../../notebooks/missions/themis/state.ipynb 15
def preprocess_sw_data(
    raw_data: pl.LazyFrame,
) -> pl.LazyFrame:
    """
    - Applying naming conventions for columns
    - Parsing and typing data (like from string to datetime for time columns)
    """

    return raw_data.with_columns(
        # Note: For `polars`, please either specify both hour and minute, or neither.
        pl.concat_str(pl.col("start"), pl.lit(" 00")).str.to_datetime(
            format="%Y %j %H %M"
        ),
        pl.concat_str(pl.col("end"), pl.lit(" 00")).str.to_datetime(
            format="%Y %j %H %M"
        ),
    )

# %% ../../../notebooks/missions/themis/state.ipynb 17
def create_sw_pipeline(sat_id="THB", source="STATE"):
    namespace = f"{sat_id}.{source}"
    node_load_sw_data = node(
        load_sw_data,
        inputs="original_sw_data",
        outputs="raw_data_sw",
        name="load_solar_wind_data",
    )
    node_preprocess_sw_state = node(
        preprocess_sw_data,
        inputs="raw_data_sw",
        outputs="inter_data_sw",
        name="preprocess_solar_wind_data",
    )
    return pipeline(
        [
            node_load_sw_data,
            node_preprocess_sw_state,
        ],
        namespace=namespace,
    )

# %% ../../../notebooks/missions/themis/state.ipynb 18
def create_pipeline(sat_id="THB", source="STATE"):

    return create_pipeline_template(
        sat_id=sat_id,
        source=source,
        load_data_fn=load_data,
        preprocess_data_fn=preprocess_data,
        process_data_fn=process_data,
    ) + create_sw_pipeline(sat_id=sat_id, source=source)
