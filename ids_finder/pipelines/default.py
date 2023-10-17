# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/99_pipelines.ipynb.

# %% auto 0
__all__ = ['process_mag_data', 'extract_features', 'create_mag_data_pipeline', 'combine_candidates']

# %% ../../notebooks/99_pipelines.ipynb 11
def process_mag_data(
    raw_data: Any | pl.DataFrame,
    ts: str = None,  # time resolution
    coord: str = None,
) -> pl.DataFrame | Dict[str, pl.DataFrame]:
    """
    Corresponding to primary data layer, where source data models are transformed into domain data models

    - Transforming data to RTN (Radial-Tangential-Normal) coordinate system
    - Smoothing data
    - Resampling data to a given time resolution
    - Partitioning data, for the sake of memory
    """
    pass

def extract_features():
    pass

# %% ../../notebooks/99_pipelines.ipynb 13
def create_mag_data_pipeline(
    sat_id: str,  # satellite id, used for namespace
    ts: str = '1s',  # time resolution,
    tau: str = '60s',  # time window
    **kwargs,
) -> Pipeline:
    
    node_download_mag_data = node(
        download_mag_data,
        inputs=dict(
            start="params:start_date",
            end="params:end_date",
        ),
        outputs=f"raw_mag",
        name=f"download_{sat_id.upper()}_magnetic_field_data",
    )

    node_preprocess_mag_data = node(
        preprocess_mag_data,
        inputs=dict(
            raw_data=f"raw_mag",
            start="params:start_date",
            end="params:end_date",
        ),
        outputs=f"inter_mag_{ts}",
        name=f"preprocess_{sat_id.upper()}_magnetic_field_data",
    )

    node_process_mag_data = node(
        process_mag_data,
        inputs=f"inter_mag_{ts}",
        outputs=f"primary_mag_rtn_{ts}",
        name=f"process_{sat_id.upper()}_magnetic_field_data",
    )

    node_extract_features = node(
        extract_features,
        inputs=[f"primary_mag_rtn_{ts}", "params:tau", "params:extract_params"],
        outputs=f"feature_tau_{tau}",
        name=f"extract_{sat_id}_features",
    )

    nodes = [
        node_download_mag_data,
        node_preprocess_mag_data,
        node_process_mag_data,
        node_extract_features,
    ]

    pipelines = pipeline(
        nodes,
        namespace=sat_id,
        parameters={
            "params:start_date": "params:jno_start_date",
            "params:end_date": "params:jno_end_date",
            "params:tau": tau,
        },
    )

    return pipelines

# %% ../../notebooks/99_pipelines.ipynb 20
def combine_candidates(dict):
    pass

# node_thm_extract_features = node(
#     extract_features,
#     inputs=["primary_thm_rtn_1s", "params:tau", "params:thm_1s_params"],
#     outputs="candidates_thm_rtn_1s",
#     name="extract_ARTEMIS_features",
# )

# node_combine_candidates = node(
#     combine_candidates,
#     inputs=dict(
#         sta_candidates="candidates_sta_rtn_1s",
#         jno_candidates="candidates_jno_ss_se_1s",
#         thm_candidates="candidates_thm_rtn_1s",
#     ),
#     outputs="candidates_all_1s",
#     name="combine_candidates",
# )