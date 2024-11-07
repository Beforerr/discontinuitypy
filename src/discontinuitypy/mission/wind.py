# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/wind.ipynb.

# %% auto 0
__all__ = ['WindConfigBase']

# %% ../../../notebooks/missions/wind.ipynb 0
from ..datasets import IDsDataset
from space_analysis.core import MagVariable
from space_analysis.meta import TempDataset, PlasmaDataset
from space_analysis.missions.wind import (
    wi_mfi_h2_bgse,
    wi_pm_3dp_ds,
    wi_plsp_3dp_ds,
    wi_elm2_3dp_ds,
)

# %% ../../../notebooks/missions/wind.ipynb 1
class WindConfigBase(IDsDataset):
    name: str = "Wind"
    mag_meta: MagVariable = wi_mfi_h2_bgse
    plasma_meta: PlasmaDataset = wi_pm_3dp_ds
    ion_temp_meta: TempDataset = wi_plsp_3dp_ds
    e_temp_meta: TempDataset = wi_elm2_3dp_ds
