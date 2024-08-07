# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/utils/05_naming.ipynb.

# %% auto 0
__all__ = ['standardize_plasma_data']

# %% ../../notebooks/utils/05_naming.ipynb 2
import polars as pl
from space_analysis.meta import PlasmaDataset
from ..naming import DENSITY_COL, TEMP_COL

# %% ../../notebooks/utils/05_naming.ipynb 3
def standardize_plasma_data(data: pl.LazyFrame, meta: PlasmaDataset):
    """
    Standardize plasma data columns across different datasets.

    Notes: meta will be updated with the new column names
    """

    mapping = dict()
    if meta.density_col:
        mapping[meta.density_col] = DENSITY_COL
        meta.density_col = DENSITY_COL
    if meta.temperature_col:
        mapping[meta.temperature_col] = TEMP_COL
        meta.temperature_col = TEMP_COL
    data = data.rename(mapping=mapping)
    return data
