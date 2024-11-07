# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/10_datasets.ipynb.

# %% auto 0
__all__ = ['IdsEvents', 'log_event_change', 'IDsDataset']

# %% ../../notebooks/10_datasets.ipynb 1
import polars as pl
from datetime import timedelta
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from beforerr.project import savename, datadir, produce_or_load, produce_or_load_file
from space_analysis.core import MagVariable
from space_analysis.meta import PlasmaDataset, TempDataset
from .utils.naming import standardize_plasma_data
from .detection.variance import detect_variance

from typing import Literal
from loguru import logger

# %% ../../notebooks/10_datasets.ipynb 3
from .utils.basic import df2ts
from .integration import update_events
from .core.pipeline import ids_finder

# %% ../../notebooks/10_datasets.ipynb 4
def select_row(df: pl.DataFrame, index: int):
    if "index" not in df.columns:
        df = df.with_row_index()
    predicate = pl.col("index") == index
    return df.row(by_predicate=predicate, named=True)

# %% ../../notebooks/10_datasets.ipynb 6
class IdsEvents(BaseModel):
    """Core class to handle discontinuity events in a dataset."""

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    name: str = None
    data: pl.LazyFrame = None
    mag_meta: MagVariable = MagVariable()

    ts: timedelta = None
    """time resolution of the dataset"""
    tau: timedelta
    """time interval used to find events"""
    events: pl.DataFrame = None
    detect_func = detect_variance
    method: Literal["fit", "derivative"] = "fit"

    file_fmt: str = "arrow"
    file_path: Path = datadir()

    def find_events(self, **kwargs):
        # To be deprecated, use `produce_or_load_file` instead
        data, _ = self.produce_or_load(**kwargs)
        self.events = data
        return self

    @property
    def file_prefix(self):
        return f"events_{self.name or ''}".removesuffix("_")

    @property
    def config_detection(self):
        return dict(
            detection_df=self.data,
            tau=self.tau,
            ts=self.ts or self.mag_meta.ts,
            method=self.method,
            bcols=self.mag_meta.B_cols,
        )

    def produce_or_load(self, **kwargs):
        config = self.config_detection | kwargs
        return produce_or_load(
            f=ids_finder,
            config=config,
            path=self.file_path,
            prefix=self.file_prefix,
            suffix=self.file_fmt,
        )

    # BUG
    @property
    def file(self):
        fname = savename(
            c=self.config_detection,
            prefix=self.file_prefix,
            suffix=self.file_fmt,
        )
        return self.file_path / fname

    def get_event(self, index: int):
        return select_row(self.events, index)

    def get_event_data(
        self,
        event,
        start_col="t.d_start",
        end_col="t.d_end",
        offset=timedelta(seconds=1),
        **kwargs,
    ):
        start = event[start_col] - offset
        end = event[end_col] + offset

        _data = self.data.filter(pl.col("time").is_between(start, end))
        return df2ts(_data, self.mag_meta.B_cols)

# %% ../../notebooks/10_datasets.ipynb 7
def log_event_change(event, logger=logger):
    logger.debug(
        f"""CHANGE INFO
        n.change: {event.get('n.change')}
        v.ion.change: {event.get('v.ion.change')}
        T.change: {event.get('T.change')}
        v.Alfven.change: {event.get('v.Alfven.change')}
        v.ion.change.l: {event.get('v.ion.change.l')}
        v.Alfven.change.l: {event.get('v.Alfven.change.l')}
        """
    )

# %% ../../notebooks/10_datasets.ipynb 8
class IDsDataset(IdsEvents):
    """Extend the IdsEvents class to handle plasma and temperature data."""

    data: pl.LazyFrame = Field(default=None, alias="mag_data")

    plasma_data: pl.LazyFrame = None
    plasma_meta: PlasmaDataset = PlasmaDataset()

    ion_temp_data: pl.LazyFrame = None
    ion_temp_meta: TempDataset = TempDataset()
    e_temp_data: pl.LazyFrame = None
    e_temp_meta: TempDataset = TempDataset()

    def plot(self, type="overview", event=None, index=None, **kwargs):
        event = event or self.get_event(index)
        if type == "overview":
            return self.overview_plot(event, **kwargs)

    @property
    def config_updates(self):
        return dict(
            plasma_data=self.plasma_data,
            plasma_meta=self.plasma_meta,
            ion_temp_data=self.ion_temp_data,
            e_temp_data=self.e_temp_data,
        )

    @property
    def file(self):
        # add prefix 'updated' to file name
        old_file = super().file
        return old_file.with_name(f"updated_{old_file.stem}{old_file.suffix}")

    def produce_or_load(self, **kwargs):
        events, file = super().produce_or_load(**kwargs)
        config = self.config_updates | dict(events=events) | kwargs
        return produce_or_load_file(f=update_events, config=config, file=self.file)

    def standardize(self):
        self.plasma_data = standardize_plasma_data(self.plasma_data, self.plasma_meta)
        return self
