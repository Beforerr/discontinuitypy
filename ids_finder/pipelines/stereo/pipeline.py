# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/stereo/index.ipynb.

# %% auto 0
__all__ = ['create_pipeline']

# %% ../../../notebooks/missions/stereo/index.ipynb 3
#| code-summary: import all the packages needed for the project
#| output: hide
from .mag import create_pipeline as create_mag_data_pipeline
from .state import create_pipeline as create_state_data_pipeline
from ..default.mission import create_combined_data_pipeline

# %% ../../../notebooks/missions/stereo/index.ipynb 6
def create_pipeline(sat_id="STA"):
    return (
        create_mag_data_pipeline(sat_id)
        + create_state_data_pipeline(sat_id)
        + create_combined_data_pipeline(sat_id)
    )