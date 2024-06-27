# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/10_datasets.ipynb.

# %% auto 0
__all__ = ['write', 'IdsEvents', 'log_event_change', 'IDsDataset']

# %% ../notebooks/10_datasets.ipynb 1
import polars as pl
# import holoviews as hv
import polars.selectors as cs
from loguru import logger
from random import sample
from datetime import timedelta

from pydantic import BaseModel, Field, validate_call
from space_analysis.meta import PlasmaDataset, TempDataset, MagDataset
from typing import Literal

# %% ../notebooks/10_datasets.ipynb 3
from .utils.basic import df2ts
from .utils.plot import plot_candidate as _plot_candidate
from .integration import combine_features, calc_combined_features
from .core.pipeline import ids_finder

# %% ../notebooks/10_datasets.ipynb 4
from pathlib import Path


def write(df: pl.DataFrame, fname: Path, format=None, **kwargs):
    if format is None:
        format = fname.suffix
        format = format[1:] if format.startswith(".") else format
    match format:
        case "arrow":
            df.write_ipc(fname, **kwargs)
        case "csv":
            df.write_csv(fname, **kwargs)
        case "parquet":
            df.write_parquet(fname, **kwargs)

    logger.info(f"Dataframe written to {fname}")

    return fname


class IdsEvents(BaseModel):
    """Core class to handle discontinuity events in a dataset."""

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

    name: str = None
    data: pl.LazyFrame = None
    ts: timedelta = None
    """time resolution of the dataset"""
    tau: timedelta = None
    """time interval used to find events"""
    events: pl.DataFrame = None
    method: Literal["fit", "derivative"] = "fit"

    @validate_call
    def export(self, path: Path, format="arrow", clean=True, **kwargs):
        if self.events is None:
            self.find_events()
        _df = self.events
        if clean:
            _df = _df.select(cs.datetime(), cs.duration(), cs.numeric())

        # check the parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        write(_df, path, format, **kwargs)
        return self

    def find_events(self, **kwargs):
        self.events = ids_finder(
            self.data, ts=self.ts, tau=self.tau, method=self.method, **kwargs
        )
        return self

    def get_event(self, index: int):
        events = self.events
        if "index" not in events.columns:
            events = events.with_row_index()
        predicate = pl.col("index") == index
        return events.row(by_predicate=predicate, named=True)

    def get_events(self, indices=None, predicate=None):
        pass

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
        return df2ts(_data, self.bcols)

# %% ../notebooks/10_datasets.ipynb 5
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

# %% ../notebooks/10_datasets.ipynb 8
class IDsDataset(IdsEvents):
    """Extend the IdsEvents class to handle plasma and temperature data."""

    data: pl.LazyFrame = Field(default=None, alias="mag_data")
    mag_meta: MagDataset = MagDataset()
    bcols: list[str] = None

    plasma_data: pl.LazyFrame = None
    plasma_meta: PlasmaDataset = PlasmaDataset()

    ion_temp_data: pl.LazyFrame = None
    ion_temp_meta: TempDataset = TempDataset()
    e_temp_data: pl.LazyFrame = None
    e_temp_meta: TempDataset = TempDataset()

    def update_events(self, **kwargs):
        return self.update_events_with_plasma_data(
            **kwargs
        ).update_events_with_temp_data(**kwargs)

    def update_events_with_plasma_data(self, **kwargs):
        # TypeError: the truth value of a LazyFrame is ambiguous
        if self.plasma_data is not None:
            df_combined = combine_features(
                self.events,
                self.plasma_data.collect(),
                plasma_meta=self.plasma_meta,
                **kwargs,
            )

            self.events = calc_combined_features(
                df_combined,
                plasma_meta=self.plasma_meta,
                **kwargs,
            )
        else:
            logger.info("Plasma data is not available.")

        return self

    def update_events_with_temp_data(self, **kwargs):
        on = "time"

        if self.ion_temp_data is not None:
            self.events = self.events.sort(on).join_asof(
                self.ion_temp_data.sort(on).collect(), on=on
            )
        else:
            logger.info("Ion temperature data is not available.")

        if self.e_temp_data is not None:
            self.events = self.events.sort(on).join_asof(
                self.e_temp_data.sort(on).collect(), on=on
            )
        else:
            logger.info("Electron temperature data is not available.")
        return self

    def plot(self, type="overview", event=None, index=None, **kwargs):

        event = event or self.get_event(index)
        if type == "overview":
            return self.overview_plot(event, **kwargs)

    def plot_candidate(self, event=None, index=None, **kwargs):
        if event is None:
            event = self.get_event(index)
        data = self.get_event_data(event, **kwargs)

        return _plot_candidate(event, data, **kwargs)

    def plot_candidates(
        self, indices=None, num=4, random=True, predicate=None, **kwargs
    ):
        events = self.events
        if "index" not in events.columns:
            events = events.with_row_index()

        if indices is None:  # the truth value of an Expr is ambiguous
            if predicate is not None:
                events = events.filter(predicate)
            indices = events.get_column("index")
            if random:
                indices = indices.sample(num).to_numpy()
            else:
                indices = indices.head(num).to_numpy()
            logger.info(f"Candidates indices: {indices}")

        return [self.plot_candidate(index=i, **kwargs) for i in indices]
