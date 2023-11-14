# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/02_stereo.ipynb.

# %% auto 0
__all__ = ['headers', 'STATE_POSITION_COLS', 'STATE_PLASMA_COLS', 'columns_name_mapping', 'download_mag_data',
           'preprocess_mag_data', 'process_mag_data', 'create_mag_data_pipeline', 'download_state_data',
           'load_state_data', 'preprocess_state_data', 'convert_state_to_rtn', 'process_state_data',
           'create_state_data_pipeline', 'create_pipeline']

# %% ../../../notebooks/missions/02_stereo.ipynb 5
#| code-summary: import all the packages needed for the project
#| output: hide
from fastcore.utils import *
from fastcore.test import *
from ...utils.basic import *
from ...core import *

import polars as pl
import pandas
import numpy as np

from datetime import timedelta
from loguru import logger

from typing import Callable, Dict

# %% ../../../notebooks/missions/02_stereo.ipynb 6
from ...core import extract_features

# %% ../../../notebooks/missions/02_stereo.ipynb 8
from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline

# %% ../../../notebooks/missions/02_stereo.ipynb 12
import os
os.environ['SPEDAS_DATA_DIR'] = f"{os.environ['HOME']}/data"
import pyspedas

# %% ../../../notebooks/missions/02_stereo.ipynb 13
def download_mag_data(
    start: str = None,
    end: str = None,
    probe: str = "a",
) -> Iterable[str]:
    trange = [start, end]
    files = pyspedas.stereo.mag(trange, downloadonly=True, probe=probe)
    return files

# %% ../../../notebooks/missions/02_stereo.ipynb 15
from ...utils.basic import cdf2pl
from pipe import select
from typing import Iterable

# %% ../../../notebooks/missions/02_stereo.ipynb 16
def preprocess_mag_data(
    raw_data: Iterable[str] = None, # List of CDF files
    ts: str = "1s",  # time resolution
) -> pl.DataFrame:
    """
    Preprocess the raw dataset (only minor transformations)

    - Downsample the data to a given time resolution
    - Applying naming conventions for columns
    """
    every = pandas.Timedelta(ts)
    period = 2 * every

    df: pl.LazyFrame = pl.concat(raw_data | pmap(cdf2pl, var_name="BFIELD"))

    return (
        df.pipe(resample, every=every, period=period)
        .rename(
            {
                "BFIELD_0": "b_r",
                "BFIELD_1": "b_t",
                "BFIELD_2": "b_n",
                "BFIELD_3": "b_mag",
            }
        )
        .collect()
    )

# %% ../../../notebooks/missions/02_stereo.ipynb 18
def process_mag_data(
    raw_data: pl.DataFrame,
    ts: str = None,  # time resolution
    coord: str = None,
) -> Dict[str, pl.DataFrame]:
    """
    Corresponding to primary data layer, where source data models are transformed into domain data models

    - Partitioning data, for the sake of memory
    """
    return partition_data_by_year(raw_data)

# %% ../../../notebooks/missions/02_stereo.ipynb 20
def create_mag_data_pipeline(
    sat_id,
    ts: str = "1s",  # time resolution,
    tau: str = "60s",  # time window
    **kwargs,
) -> Pipeline:
    node_download_data = node(
        download_mag_data,
        inputs=dict(
            start="params:start_date",
            end="params:end_date",
        ),
        outputs=f"raw_mag_files",
        name=f"download_{sat_id.upper()}_magnetic_field_data",
    )

    node_preprocess_data = node(
        preprocess_mag_data,
        inputs=dict(
            raw_data=f"raw_mag_files",
        ),
        outputs=f"inter_mag_{ts}",
        name=f"preprocess_{sat_id.upper()}_magnetic_field_data",
    )

    node_process_data = node(
        process_mag_data,
        inputs=f"inter_mag_{ts}",
        outputs=f"primary_mag_{ts}",
        name=f"process_{sat_id.upper()}_magnetic_field_data",
    )

    node_extract_features = node(
        extract_features,
        inputs=[f"primary_mag_{ts}", "params:tau", "params:extract_params"],
        outputs=f"feature_tau_{tau}",
        name=f"extract_{sat_id}_features",
    )

    nodes = [
        node_download_data,
        node_preprocess_data,
        node_process_data,
        node_extract_features,
    ]

    pipelines = pipeline(
        nodes,
        namespace=sat_id,
        parameters={
            "params:start_date": "params:jno_start_date",
            "params:end_date": "params:jno_end_date",
            "params:tau": "params:tau",
        },
    )

    return pipelines

# %% ../../../notebooks/missions/02_stereo.ipynb 23
import pooch
from pipe import select

# %% ../../../notebooks/missions/02_stereo.ipynb 24
def download_state_data(
    start: str = None,
    end: str = None,
) -> List[str]:
    download = partial(pooch.retrieve, known_hash=None)

    start_time = pandas.Timestamp(start)
    end_time = pandas.Timestamp(end)

    url = "https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/merged/stereoa{year}.asc"

    files = list(
        range(start_time.year, end_time.year + 1)
        | select(lambda x: url.format(year=x))
        | select(download)
    )
    return files

# %% ../../../notebooks/missions/02_stereo.ipynb 25
headers = """Year
DOY
Hour
Radial Distance, AU
HGI Lat. of the S/C
HGI Long. of the S/C
IMF BR, nT (RTN)
IMF BT, nT (RTN)
IMF BN, nT (RTN)
IMF B Scalar, nT
SW Plasma Speed, km/s
SW Lat. Angle RTN, deg.
SW Long. Angle RTN, deg.
SW Plasma Density, N/cm^3
SW Plasma Temperature, K
1.8-3.6 MeV H flux,LET
4.0-6.0 MeV H flux,LET
6.0-10.0 MeV H flux, LET
10.0-12.0 MeV H flux,LET
13.6-15.1 MeV H flux, HET
14.9-17.1 MeV H flux, HET
17.0-19.3 MeV H flux, HET
20.8-23.8 MeV H flux, HET
23.8-26.4 MeV H flux, HET
26.3-29.7 MeV H flux, HET
29.5-33.4 MeV H flux, HET
33.4-35.8 MeV H flux, HET
35.5-40.5 MeV H flux, HET
40.0-60.0 MeV H flux, HET
60.0-100.0 MeV H flux, HET
0.320-0.452 MeV H flux, SIT
0.452-0.64 MeV H flux, SIT
0.640-0.905 MeV H flux, SIT
0.905-1.28 MeV H flux, SIT
1.280-1.81 MeV H flux, SIT
1.810-2.56 MeV H flux, SIT
2.560-3.62 MeV H flux, SIT"""

def load_state_data(
    start: str = None,
    end: str = None,
) -> pl.DataFrame:
    """
    - Downloading data
    - Reading data into a proper data structure, like dataframe.
        - Parsing original data (dealing with delimiters, missing values, etc.)
    """
    files = download_state_data(start, end)
    
    labels = headers.split("\n")
    missing_values = ["999.99", "9999.9", "9999999."]

    df = pl.concat(
        files
        | pmap(
            pandas.read_csv,
            delim_whitespace=True,
            names=labels,
            na_values=missing_values,
        )
        | select(pl.from_pandas)
    )
    
    return df


# %% ../../../notebooks/missions/02_stereo.ipynb 27
def preprocess_state_data(
    raw_data: pl.DataFrame,
    ts: str = None,  # time resolution
    coord: str = None,
) -> pl.DataFrame:
    """
    Preprocess the raw dataset (only minor transformations)

    - Parsing and typing data (like from string to datetime for time columns)
    - Changing storing format (like from `csv` to `parquet`)
    """

    return raw_data.with_columns(
        time=(
            pl.datetime(pl.col("Year"), month=1, day=1)
            + pl.duration(days=pl.col("DOY") - 1, hours=pl.col("Hour"))
        ).dt.cast_time_unit("ns"),
    )

# %% ../../../notebooks/missions/02_stereo.ipynb 29
def convert_state_to_rtn(df: pl.DataFrame) -> pl.DataFrame:
    """Convert state data to RTN coordinates"""
    plasma_speed = pl.col("plasma_speed")
    sw_elevation = pl.col("sw_elevation").radians()
    sw_azimuth = pl.col("sw_azimuth").radians()
    return df.with_columns(
        sw_vel_r=plasma_speed * sw_elevation.cos() * sw_azimuth.cos(),
        sw_vel_t=plasma_speed * sw_elevation.cos() * sw_azimuth.sin(),
        sw_vel_n=plasma_speed * sw_elevation.sin(),
    ).drop(["sw_elevation", "sw_azimuth"])


STATE_POSITION_COLS = [
    "Radial Distance, AU",
    "HGI Lat. of the S/C",
    "HGI Long. of the S/C",
]

STATE_PLASMA_COLS = [
    "SW Plasma Speed, km/s",
    "SW Lat. Angle RTN, deg.",
    "SW Long. Angle RTN, deg.",
    "SW Plasma Density, N/cm^3",
    "SW Plasma Temperature, K",
]

columns_name_mapping = {
    "SW Plasma Speed, km/s": "plasma_speed",
    "SW Lat. Angle RTN, deg.": "sw_elevation",
    "SW Long. Angle RTN, deg.": "sw_azimuth",
    "SW Plasma Density, N/cm^3": "plasma_density",
    "SW Plasma Temperature, K": "plasma_temperature",
    "Radial Distance, AU": "radial_distance",
}


def process_state_data(
    df: pl.DataFrame, columns: list[str] = STATE_POSITION_COLS + STATE_PLASMA_COLS
) -> pl.DataFrame:
    """
    Corresponding to primary data layer, where source data models are transformed into domain data models

    - Applying naming conventions for columns
    - Transforming data to RTN (Radial-Tangential-Normal) coordinate system
    - Discarding unnecessary columns
    """

    return (
        df.select("time", *columns)
        .rename(columns_name_mapping)
        .pipe(convert_state_to_rtn)
        .rename(
            {
                "sw_vel_r": "v_x",
                "sw_vel_t": "v_y",
                "sw_vel_n": "v_z",
            }
        )
    )

# %% ../../../notebooks/missions/02_stereo.ipynb 31
def create_state_data_pipeline(
    sat_id = 'sta',
    ts: str = '1h',  # time resolution
    **kwargs
) -> Pipeline:
    
    node_load_data = node(
        load_state_data,
        inputs=dict(
            start="params:start_date",
            end="params:end_date",
        ),
        outputs=f"raw_state",
        name=f"load_{sat_id.upper()}_state_data",
    )

    node_preprocess_data = node(
        preprocess_state_data,
        inputs=dict(
            raw_data=f"raw_state",
        ),
        outputs=f"inter_state_{ts}",
        name=f"preprocess_{sat_id.upper()}_state_data",
    )
    
    node_process_data = node(
        process_state_data,
        inputs=f"inter_state_{ts}",
        outputs=f"primary_state_{ts}",
        name=f"process_{sat_id.upper()}_state_data",
    )
    
    nodes = [
        node_load_data,
        node_preprocess_data,
        node_process_data,
    ]
    pipelines = pipeline(
        nodes,
        namespace=sat_id,
        parameters={
            "params:start_date": "params:jno_start_date",
            "params:end_date": "params:jno_end_date",
        },
    )

    return pipelines

# %% ../../../notebooks/missions/02_stereo.ipynb 33
from ..default import create_candidate_pipeline

# %% ../../../notebooks/missions/02_stereo.ipynb 34
def create_pipeline(
    sat_id="sta",
    tau="60s",
    ts_mag="1s",  # time resolution of magnetic field data
    ts_state="1h",  # time resolution of state data
) -> Pipeline:
    return (
        create_mag_data_pipeline(sat_id, ts=ts_mag, tau=tau)
        + create_state_data_pipeline(sat_id, ts=ts_state)
        + create_candidate_pipeline(sat_id, tau=tau, ts_state=ts_state)
    )
