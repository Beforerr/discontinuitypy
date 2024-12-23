# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/missions/stereo.ipynb.

# %% auto 0
__all__ = ['StereoConfigBase']

# %% ../../../notebooks/missions/stereo.ipynb 0
from ..datasets import IDsDataset
from space_analysis.meta import MagDataset, PlasmaDataset
from space_analysis.missions.stereo import sta_l1_mag_rtn, sta_l2_pla

# %% ../../../notebooks/missions/stereo.ipynb 1
class StereoConfigBase(IDsDataset):
    name: str = "STEREO"
    mag_meta: MagDataset = sta_l1_mag_rtn
    plasma_meta: PlasmaDataset = sta_l2_pla
