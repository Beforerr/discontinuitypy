# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/pipelines/1_data.ipynb.

# %% auto 0
__all__ = ['DEFAULT_LOAD_INPUTS', 'create_pipeline_template']

# %% ../../../notebooks/pipelines/1_data.ipynb 1
import polars as pl

from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline
from typing import Callable, Optional, Any, Dict

# %% ../../../notebooks/pipelines/1_data.ipynb 11
from ... import PARAMS

DEFAULT_LOAD_INPUTS = dict(
    start="params:start_date",
    end="params:end_date",
    datatype="params:datatype",
)

# %% ../../../notebooks/pipelines/1_data.ipynb 12
from semver import process


def create_pipeline_template(
    sat_id: str,  # satellite id, used for namespace
    source: str,  # source data, like "mag" or "plasma", used for namespace
    load_data_fn: Callable,
    preprocess_data_fn: Callable,
    process_data_fn: Callable,
    load_inputs: dict = DEFAULT_LOAD_INPUTS,
    process_inputs: dict = None,
    params: Optional[dict] = None,
    **kwargs,
) -> Pipeline:
    if params is None:
        params = PARAMS

    namespace = f"{sat_id}.{source}"

    ts = params[sat_id][source]["time_resolution"]
    datatype = params[sat_id][source]["datatype"]

    ts_str = f"ts_{ts}s"

    if process_inputs is None:
        process_inputs = dict(
            raw_data=f"inter_data_{datatype}",
            ts="params:time_resolution",
        )

    node_load_data = node(
        load_data_fn,
        inputs=load_inputs,
        outputs="raw_data",
        name="load_data",
    )

    node_preprocess_data = node(
        preprocess_data_fn,
        inputs="raw_data",
        outputs=f"inter_data_{datatype}",
        name="preprocess_data",
    )

    node_process_data = node(
        process_data_fn,
        inputs=process_inputs,
        outputs=f"primary_data_{ts_str}",
        name="process_data",
    )

    nodes = [
        node_load_data,
        node_preprocess_data,
        node_process_data,
    ]

    pipelines = pipeline(
        nodes,
        namespace=namespace,
        parameters={
            "params:start_date": "params:jno_start_date",
            "params:end_date": "params:jno_end_date",
        },
    )

    return pipelines
