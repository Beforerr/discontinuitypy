# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/juno/index.ipynb.

# %% auto 0
__all__ = ['create_pipeline']

# %% ../../../notebooks/missions/juno/index.ipynb 9
#| code-summary: import all the packages needed for the project
#| output: hide
from .mag import create_pipeline as create_mag_data_pipeline
from .state import create_pipeline as create_state_data_pipeline
from ..default.mission import create_combined_data_pipeline

# %% ../../../notebooks/missions/juno/index.ipynb 12
def create_pipeline(sat_id="JNO"):
    return (
        create_mag_data_pipeline(sat_id)
        + create_state_data_pipeline(sat_id)
        + create_combined_data_pipeline(sat_id)
    )
