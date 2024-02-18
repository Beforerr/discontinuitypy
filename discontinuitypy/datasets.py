# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/10_datasets.ipynb.

# %% auto 0
__all__ = ['IdsEvents', 'log_event_change', 'IDsDataset']

# %% ../notebooks/10_datasets.ipynb 1
import polars as pl
import hvplot.polars
import holoviews as hv
import polars.selectors as cs
from loguru import logger
from random import sample
from datetime import timedelta

from pydantic import BaseModel, Field

# %% ../notebooks/10_datasets.ipynb 4
from .utils.basic import df2ts
from .utils.plot import plot_candidate as _plot_candidate
from .integration import combine_features, calc_combined_features
from .core.pipeline import ids_finder

# %% ../notebooks/10_datasets.ipynb 5
class IdsEvents(BaseModel):
    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

    name: str = None
    events: pl.DataFrame = None

    data: pl.LazyFrame = None
    ts: timedelta = None
    """time resolution of the dataset"""
    tau: timedelta = None
    """time interval used to find events"""

    def export(self, path, format="arrow", clean=True, **kwargs):
        if self.events is None:
            self.find_events()
        _df = self.events
        if clean:
            _df = _df.select(cs.datetime(), cs.duration(), cs.numeric())

        match format:
            case "arrow":
                _df.write_ipc(path, **kwargs)
            case "csv":
                _df.write_csv(path, **kwargs)
            case "parquet":
                _df.write_parquet(path, **kwargs)
        return self

    def find_events(self, **kwargs):
        self.events = ids_finder(self.data, ts=self.ts, tau=self.tau, **kwargs)
        return self

    def get_event(self, index=None, predicates=None, random: bool = True, **kwargs):
        if index:
            candidate = self.events.row(index, named=True)
        elif predicates:
            candidate = self.events.filter(predicates).row(0, named=True)
        else:
            index = sample(range(len(self.events)), 1)[0] if random else 0
            candidate = self.events.row(index, named=True)
        return candidate

    def get_event_data(self, candidate=None, index=None, predicates=None, **kwargs):
        if candidate is None:
            candidate = self.get_event(index, predicates, **kwargs)

        _data = self.data.filter(
            pl.col("time").is_between(candidate["tstart"], candidate["tstop"])
        )
        return df2ts(_data, self.bcols)

# %% ../notebooks/10_datasets.ipynb 6
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

# %% ../notebooks/10_datasets.ipynb 7
class IDsDataset(IdsEvents):

    data: pl.LazyFrame = Field(default=None, alias="mag_data")
    plasma_data: pl.LazyFrame = None

    bcols: list[str] = None
    vec_cols: list[str] = None

    density_col: str = None  # "n"
    speed_col: str = None  # "v"
    temperature_col: str = None  # "T"
    plasma_meta: dict = None

    def update_candidates_with_plasma_data(self, **kwargs):
        subset_cols = []
        if self.vec_cols:
            subset_cols.extend(self.vec_cols)
        if self.density_col:
            subset_cols.append(self.density_col)
        if self.speed_col:
            subset_cols.append(self.speed_col)
        if self.temperature_col:
            subset_cols.append(self.temperature_col)

        df_combined = combine_features(
            self.events,
            self.plasma_data.collect(),
            subset_cols=subset_cols,
            **kwargs,
        )

        self.events = calc_combined_features(
            df_combined,
            vec_cols=self.vec_cols,
            density_col=self.density_col,
            temperature_col=self.temperature_col,
            **kwargs,
        )
        return self

    def plot(self, type="overview", event=None, index=None, predicates=None, **kwargs):

        event = event or self.get_event(index, predicates, **kwargs)
        if type == "overview":
            return self.overview_plot(event, **kwargs)

    def overview_plot(
        self, event: dict, start=None, stop=None, offset=timedelta(seconds=1), **kwargs
    ):
        start = start or event["tstart"]
        stop = stop or event["tstop"]

        start -= offset
        stop += offset

        _plasma_data = self.plasma_data.filter(
            pl.col("time").is_between(start, stop)
        ).collect()

        _mag_data = (
            self.data.filter(pl.col("time").is_between(start, stop))
            .collect()
            .melt(
                id_vars=["time"],
                value_vars=self.bcols,
                variable_name="B comp",
                value_name="B",
            )
        )

        v_df = _plasma_data.melt(
            id_vars=["time"],
            value_vars=self.vec_cols,
            variable_name="veloity comp",
            value_name="v",
        )

        panel_mag = _mag_data.hvplot(
            x="time", y="B", by="B comp", ylabel="Magnetic Field", **kwargs
        )
        panel_n = _plasma_data.hvplot(
            x="time", y=self.density_col, **kwargs
        ) * _plasma_data.hvplot.scatter(x="time", y=self.density_col, **kwargs)

        panel_v = v_df.hvplot(
            x="time", y="v", by="veloity comp", ylabel="Plasma Velocity", **kwargs
        )
        panel_temp = _plasma_data.hvplot(x="time", y=self.temperature_col, **kwargs)

        mag_vlines = hv.VLine(event["d_tstart"]) * hv.VLine(event["d_tstop"])
        plasma_vlines = hv.VLine(event.get("time_before")) * hv.VLine(
            event.get("time_after")
        )

        logger.info(f"Overview plot: {event['tstart']} - {event['tstop']}")
        log_event_change(event)

        return (
            panel_mag * mag_vlines
            + panel_n * plasma_vlines
            + panel_v * plasma_vlines
            + panel_temp * plasma_vlines
        ).cols(1)

    def plot_candidate(self, candidate=None, index=None, predicates=None, **kwargs):
        if candidate is None:
            candidate = self.get_event(index, predicates, **kwargs)
        sat_fgm = self.get_event_data(candidate)

        return _plot_candidate(candidate, sat_fgm, **kwargs)

    def plot_candidates(
        self, indices=None, num=4, random=True, predicates=None, **kwargs
    ):
        events = self.events.with_row_index()

        if indices is None: # the truth value of an Expr is ambiguous
            if predicates is not None:
                events = events.filter(predicates)
            indices = events.get_column("index")
            if random:
                indices = indices.sample(num).to_numpy()
            else:
                indices = indices.head(num).to_numpy()
            logger.info(f"Candidates indices: {indices}")

        return [self.plot_candidate(index=i, **kwargs) for i in indices]
