# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/11_ids_config.ipynb.

# %% auto 0
__all__ = ['standardize_plasma_data', 'IDsConfig', 'SpeasyIDsConfig']

# %% ../notebooks/11_ids_config.ipynb 0
from datetime import datetime
from .datasets import IDsDataset
from space_analysis.ds.meta import Meta, PlasmaMeta
from space_analysis.utils.speasy import Variables
import polars as pl

from pathlib import Path

from tqdm.auto import tqdm

# %% ../notebooks/11_ids_config.ipynb 1
def standardize_plasma_data(data: pl.LazyFrame, meta: PlasmaMeta):
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
    
    def export(self, **kwargs):
        return super().export(self.path, format=self.fmt, **kwargs)

    def load(self):
        if self.path.exists():
            self.events = pl.read_ipc(self.path)
        return self
    
    def _get_and_process_data(self, **kwargs) -> pl.DataFrame:
        pass

    def get_and_process_data(self, **kwargs):
        self.events = pl.concat(self._get_and_process_data(**kwargs))
        return self

# %% ../notebooks/11_ids_config.ipynb 3
class SpeasyIDsConfig(IDsConfig):
    """Based on `speasy` Variables to get the data"""
    _cached_vars: dict[str, Variables] = {}
    
    def model_post_init(self, __context):
        # TODO: directly get columns from the data without loading them
        # self.plasma_meta.density_col = self.plasma_vars.data[0].columns[0]
        # self.plasma_meta.velocity_cols = self.plasma_vars.data[1].columns
        pass

    def get_vars(self, vars: str):
        meta: Meta = getattr(self, f"{vars}_meta")
        return Variables(
            timerange=self.timerange,
            **meta.model_dump(),
        )

    def get_cached_vars(self, vars: str):
        if vars not in self._cached_vars:
            self._cached_vars[vars] = self.get_vars(vars)
        return self._cached_vars[vars]


    @property
    def mag_vars(self):
        return self.get_cached_vars("mag")

    @property
    def plasma_vars(self):
        return self.get_cached_vars("plasma")

    @property
    def timeranges(self):
        from sunpy.time import TimeRange

        trs: list[TimeRange] = TimeRange(self.timerange).split(self.split)
        return [[tr.start.value, tr.end.value] for tr in trs]

    def _get_and_process_data(self, **kwargs):
        self.plasma_meta.density_col = self.plasma_vars.data[0].columns[0]
        self.plasma_meta.velocity_cols = self.plasma_vars.data[1].columns
        for tr in tqdm(self.timeranges):
            ids_ds = self.model_copy(update={"timerange": tr, "split": 1}, deep=True)
            
            ids_ds.data = ids_ds.get_vars("mag").retrieve_data().to_polars()
            ids_ds.plasma_data = (
                ids_ds.get_vars("plasma")
                .retrieve_data()
                .to_polars()
                .pipe(standardize_plasma_data, ids_ds.plasma_meta)
            )
            
            yield ids_ds.find_events(
                return_best_fit=False
            ).update_candidates_with_plasma_data().events
