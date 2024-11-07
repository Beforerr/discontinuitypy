# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/solo.ipynb.

# %% auto 0
__all__ = ['SoloConfigBase']

# %% ../../../notebooks/missions/solo.ipynb 0
from ..datasets import IDsDataset
from space_analysis.meta import MagDataset, PlasmaDataset
from space_analysis.missions.solo import (
    solo_l2_mag_rtn_normal,
    solo_l2_swa_pas_grnd_mom,
)

# %% ../../../notebooks/missions/solo.ipynb 1
class SoloConfigBase(IDsDataset):
    name: str = "Solo"
    mag_meta: MagDataset = solo_l2_mag_rtn_normal
    plasma_meta: PlasmaDataset = solo_l2_swa_pas_grnd_mom