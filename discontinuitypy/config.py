# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/11_ids_config.ipynb.

# %% auto 0
__all__ = ['standardize_plasma_data', 'IDsConfig', 'SpeasyIDsConfig']

# %% ../notebooks/11_ids_config.ipynb 0
from datetime import datetime
from .datasets import IDsDataset
from space_analysis.meta import MagDataset, PlasmaDataset
from space_analysis.utils.speasy import Variables
import polars as pl
from loguru import logger
from pathlib import Path
from functools import cached_property

from tqdm.auto import tqdm

# %% ../notebooks/11_ids_config.ipynb 1
def standardize_plasma_data(data: pl.LazyFrame, meta: PlasmaDataset):
    """
    Standardize plasma data columns across different datasets.
    
    Notes: meta will be updated with the new column names
    """

    if meta.density_col:
        data = data.rename({meta.density_col: "plasma_density"})
        meta.density_col = "plasma_density"
    return data

# %% ../notebooks/11_ids_config.ipynb 2
class IDsConfig(IDsDataset):
    """
    Extend the IDsDataset class to provide additional functionalities:
    
    - Export and load data
    - Standardize data
    - Split data to handle large datasets
    """
    timerange: list[datetime] = None

    split: int = 1
    fmt: str = "arrow"
    
    _data_dir = Path("data")
    
    @property
    def fname(self):
        ts_str = f"ts_{self.ts.total_seconds():.2f}s"
        tau_str = f"tau_{self.tau.total_seconds():.0f}s"
        return f"events.{self.name}.{self.method}.{ts_str}_{tau_str}.{self.fmt}"

    @property
    def path(self):
        return self._data_dir / self.fname
    
    @property
    def timeranges(self):
        from sunpy.time import TimeRange

        trs: list[TimeRange] = TimeRange(self.timerange).split(self.split)
        return [[tr.start.value, tr.end.value] for tr in trs]
    
    def export(self, **kwargs):
        return super().export(self.path, format=self.fmt, **kwargs)

    def load(self):
        if self.path.exists():
            logger.info(f"Loading data from {self.path}")
            self.events = pl.read_ipc(self.path)
        else:
            logger.warning(f"Data not found at {self.path}")
        return self

# %% ../notebooks/11_ids_config.ipynb 3
class SpeasyIDsConfig(IDsConfig):
    """Based on `speasy` Variables to get the data"""
    provider: str = "cda"

    def model_post_init(self, __context):
        # TODO: directly get columns from the data without loading them
        # self.plasma_meta.density_col = self.plasma_vars.data[0].columns[0]
        # self.plasma_meta.velocity_cols = self.plasma_vars.data[1].columns
        pass

    def get_vars(self, vars: str):
        meta: Meta = getattr(self, f"{vars}_meta")
        return Variables(
            timerange=self.timerange,
            provider=self.provider,
            **meta.model_dump(exclude_unset=True),
        )

    def get_vars_df(self, vars: str, cached: bool = False):
        if not cached:
            return self.get_vars(vars).to_polars()
        else:
            return NotImplementedError

    # Variables
    @cached_property
    def mag_vars(self):
        return self.get_vars("mag")

    @cached_property
    def plasma_vars(self):
        return self.get_vars("plasma")

    @cached_property
    def ion_temp_var(self):
        return self.get_vars("ion_temp")

    @cached_property
    def e_temp_var(self):
        return self.get_vars("e_temp")

    # DataFrames
    def set_data_from_vars(self, update: False):
        pass

    def _get_and_process_data(self, **kwargs):
        self.plasma_meta.density_col = self.plasma_vars.data[0].columns[0]
        self.plasma_meta.velocity_cols = self.plasma_vars.data[1].columns

        # TODO: optimize for no-split timeranges

        for tr in tqdm(self.timeranges):
            ids_ds = self.model_copy(update={"timerange": tr, "split": 1}, deep=True)

            ids_ds.data = ids_ds.get_vars_df("mag", cached=False)
            ids_ds.plasma_data = ids_ds.get_vars_df("plasma", cached=False).pipe(
                standardize_plasma_data, ids_ds.plasma_meta
            )

            yield ids_ds.find_events(
                return_best_fit=False
            ).update_events_with_plasma_data().events
            
    def get_and_process_data(self, **kwargs):
        self.events = pl.concat(self._get_and_process_data(**kwargs))
        return self
