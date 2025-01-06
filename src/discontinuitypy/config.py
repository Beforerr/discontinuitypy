# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/11_ids_config.ipynb.

# %% auto 0
__all__ = ['split_timerange', 'IDsConfig', 'get_vars', 'SpeasyIDsConfig']

# %% ../../notebooks/11_ids_config.ipynb 0
from datetime import datetime
from beforerr.project import produce_or_load_file
from .datasets import IDsDataset
from space_analysis.meta import Dataset
from space_analysis.utils.speasy import Variables, get_data, get_time_resolution
from space_analysis.ds.spz.io import spzvars2pldf
import polars as pl
from functools import cached_property

from tqdm.auto import tqdm
from loguru import logger

# %% ../../notebooks/11_ids_config.ipynb 1
def split_timerange(timerange: list[datetime], n: int = 1):
    """
    Split a timerange into multiple timeranges.

    Reference: `TimeRange` in `sunpy.time`
    """
    if n <= 0:
        raise ValueError("n must be greater than or equal to 1")
    subtimeranges = []
    previous_time = timerange[0]
    dt = timerange[1] - timerange[0]
    next_time = None
    for _ in range(n):
        next_time = previous_time + dt / n
        next_range = [previous_time, next_time]
        subtimeranges.append(next_range)
        previous_time = next_time
    return subtimeranges

# %% ../../notebooks/11_ids_config.ipynb 2
def _timerange2str(timerange: list[datetime]):
    return "_tr=" + "-".join(t.strftime("%Y%m%d") for t in timerange)


class IDsConfig(IDsDataset):
    """
    Extend the IDsDataset class to provide additional functionalities:

    - Split data to handle large datasets (thus often requiring getting data lazily)
    """

    timerange: list[datetime] = None
    split: int = 1
    tmp: bool = False  # temporary flag

    @property
    def timeranges(self):
        return split_timerange(self.timerange, self.split)

    @property
    def _file_prefix(self):
        tr_str = _timerange2str(self.timerange) if self.timerange else ""
        _fp = self.name + tr_str
        return "_" + _fp if self.tmp else _fp

    def update_timerange(self, timerange, **kwargs):
        update = dict(timerange=timerange) | kwargs
        return self.model_copy(update=update, deep=True)

    @property
    def splitted_configs(self):
        update_kw = dict(tmp=True, split=1)
        return [self.update_timerange(tr, **update_kw) for tr in self.timeranges]

    def _func(self, force=False, **kwargs):
        configs = self.splitted_configs
        datas, _ = zip(
            *(c.produce_or_load(force=force, **kwargs) for c in tqdm(configs))
        )
        return pl.concat(datas)

    def produce_or_load(self, force=False, **kwargs):
        config = dict(force=force, **kwargs)
        if self.split == 1:
            if force or not self.file.exists():
                self.get_data()
            return super().produce_or_load(**config)
        else:
            return produce_or_load_file(
                f=self._func,
                config=config,
                file=self.file,
                force=force,
            )

    def get_data(self):
        pass

# %% ../../notebooks/11_ids_config.ipynb 3
def get_vars(self, vars: str, timerange: list[datetime] = None):
    meta: Dataset = getattr(self, f"{vars}_meta")
    timerange = timerange or self.timerange or meta.timerange
    return Variables(
        timerange=timerange,
        provider=self.provider,
        **meta.model_dump(exclude_unset=True),
    )


class SpeasyIDsConfig(IDsConfig):
    """Based on `speasy` Variables to get the data"""

    provider: str = "cda"

    def get_vars(self, *args, **kwargs):
        return get_vars(self, *args, **kwargs)

    def get_vars_df(self, vars: str, **kwargs):
        return get_vars(self, vars, **kwargs).to_polars()

    @cached_property
    def plasma_vars(self):
        return self.get_vars("plasma")

    def get_data(self):
        return self._get_mag_data()._get_plasma_data()

    def _get_plasma_data(self):
        # TODO: directly get columns from the data without loading them
        plasma_vars = self.plasma_vars
        pm = self.plasma_meta
        pm.density_col = pm.density_col or plasma_vars.data[0].columns[0]
        pm.velocity_cols = pm.velocity_cols or plasma_vars.data[1].columns
        pm.temperature_col = pm.temperature_col or plasma_vars.data[-1].columns[0]
        self.plasma_data = self.plasma_data or self.get_vars_df("plasma")
        return self

    def _get_mag_data(self):
        if self.data is None:
            data = get_data(self.mag_meta, self.provider, self.timerange)
            self.mag_meta.data = data
            if self.mag_meta.ts is None:
                ts = get_time_resolution(data[0])["median"]
                logger.info(f"Setting time resolution to {ts}")
                self.mag_meta.ts = ts
            self.data = spzvars2pldf(data)
        return self
