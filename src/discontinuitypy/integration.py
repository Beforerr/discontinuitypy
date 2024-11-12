# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/03_mag_plasma.ipynb.

# %% auto 0
__all__ = ['interpolate_arr_dtype', 'interpolate', 'interpolate2', 'combine_features', 'calc_combined_features',
           'update_events_with_plasma_data', 'update_events_with_temp_data', 'update_events',
           'calc_plasma_parameter_change']

# %% ../../notebooks/03_mag_plasma.ipynb 1
import polars as pl
import polars.selectors as cs
from beforerr.polars import format_time
from space_analysis.plasma.formulary.polars import (
    df_Alfven_speed,
    df_Alfven_current,
    df_inertial_length,
    df_gradient_current,
)
from space_analysis.meta import PlasmaDataset
from .utils.ops import vector_project_pl
from typing_extensions import deprecated
from . import UPSTREAM_TIME, DOWNSTREAM_TIME
from .naming import DENSITY_COL, VELOCITY_COL, TEMP_COL, FIT_AMPL_COL
from .utils.naming import standardize_plasma_data
from loguru import logger

# %% ../../notebooks/03_mag_plasma.ipynb 2
@deprecated("Not used anymore")
def _interpolate(
    df: pl.DataFrame, on="time", method="index", limit=1, limit_direction="both"
):
    # Note: limit is set to 1 to improve the confidence of the interpolation
    # Related: https://github.com/pola-rs/polars/issues/9616
    return pl.from_pandas(
        df.to_pandas()
        .set_index(on)
        .sort_index()
        .interpolate(
            method=method,
            limit=limit,
            limit_direction=limit_direction,
        )
    )


def _interpolate_arr(df: pl.DataFrame, col, on):
    width = df[col].dtype.size
    return df.with_columns(
        pl.concat_list(pl.col(col).arr.to_struct().struct.unnest().interpolate_by(on))
        .list.to_array(width)
        .alias(col)
    )


def _select_arr_dtype(df: pl.DataFrame, dtype=pl.Array):
    return [col for col in df.columns if df[col].dtype.base_type() is dtype]


def interpolate_arr_dtype(df: pl.DataFrame, on):
    for col in _select_arr_dtype(df):
        df = _interpolate_arr(df, col, on)
    return df


def interpolate(df: pl.DataFrame, on="time"):
    return (
        df.sort(on)
        .with_columns(cs.numeric().interpolate_by(on))
        .pipe(interpolate_arr_dtype, on)
        .unique(on)
        .sort(on)
    )


def interpolate2(df1: pl.DataFrame, df2, **kwargs):
    return pl.concat([df1, df2], how="diagonal_relaxed").pipe(interpolate, **kwargs)

# %% ../../notebooks/03_mag_plasma.ipynb 4
def combine_features(
    events: pl.DataFrame,
    states_data: pl.DataFrame,
    method: str = "interpolate",
    left_on="t.d_time",
    right_on="time",
    subset=False,
):
    if subset:
        subset_cols = [DENSITY_COL, TEMP_COL, right_on]
        states_data = states_data.select(subset_cols)

    # change time format: see issue: https://github.com/pola-rs/polars/issues/12023
    states_data = states_data.pipe(format_time).sort(right_on)
    events = events.pipe(format_time).sort(left_on)

    df = events.join_asof(
        states_data, left_on=left_on, right_on=right_on, strategy="nearest"
    ).drop(right_on + "_right")

    if method == "interpolate":
        before_df = interpolate2(df.select(time=pl.col(UPSTREAM_TIME)), states_data)
        after_df = interpolate2(df.select(time=pl.col(DOWNSTREAM_TIME)), states_data)
        return (
            df.sort(UPSTREAM_TIME)
            .join(
                before_df,
                left_on=UPSTREAM_TIME,
                right_on=right_on,
                suffix=".before",
            )
            .sort(DOWNSTREAM_TIME)
            .join(
                after_df,
                left_on=DOWNSTREAM_TIME,
                right_on=right_on,
                suffix=".after",
            )
        )

    elif method == "nearest":
        return (
            df.sort(UPSTREAM_TIME)
            .join_asof(
                states_data,
                left_on=UPSTREAM_TIME,
                right_on=right_on,
                strategy="backward",
                suffix=".before",
            )
            .sort(DOWNSTREAM_TIME)
            .join_asof(
                states_data,
                left_on=DOWNSTREAM_TIME,
                right_on=right_on,
                strategy="forward",
                suffix=".after",
            )
        )
    else:
        return df

# %% ../../notebooks/03_mag_plasma.ipynb 7
def calc_combined_features(df: pl.DataFrame, b_norm_col="b_mag"):
    """Calculate the combined features of the discontinuity

    Parameters
    ----------
    df : pl.DataFrame
        Input dataframe with discontinuity data
    b_norm_col :
        Column name for mean magnetic field magnitude
    """
    return (
        df.pipe(vector_project_pl, VELOCITY_COL, "n_cross", name="V_n_cross")
        .with_columns(L_n_cross=pl.col("V_n_cross").abs() * pl.col("duration"))
        .pipe(
            df_gradient_current, B_gradient="d_star", speed="V_n_cross", col_name="j0_k"
        )  # TODO: d_star corresponding to dB/dt, which direction is not exactly perpendicular to the k direction
        .pipe(df_inertial_length, density=DENSITY_COL)
        .pipe(df_Alfven_speed, B=b_norm_col, density=DENSITY_COL)
        .pipe(df_Alfven_current, density=DENSITY_COL)
    )

# %% ../../notebooks/03_mag_plasma.ipynb 8
def update_events_with_plasma_data(
    events: pl.DataFrame,
    plasma_data: pl.LazyFrame | None,
    **kwargs,
):
    if plasma_data is not None:
        events = combine_features(events, plasma_data.collect(), **kwargs)
        events = calc_combined_features(events, **kwargs)
    else:
        logger.info("Plasma data is not available.")

    return events

# %% ../../notebooks/03_mag_plasma.ipynb 9
def update_events_with_temp_data(
    events: pl.DataFrame,
    ion_temp_data: pl.LazyFrame | None,
    e_temp_data: pl.LazyFrame | None,
):
    left_on = "t.d_time"
    right_on = "time"

    events = events.pipe(format_time).sort(left_on)

    if ion_temp_data is not None:
        ion_temp_data = ion_temp_data.pipe(format_time).sort(right_on)
        events = events.join_asof(
            ion_temp_data.collect(), left_on=left_on, right_on=right_on
        ).drop(right_on + "_right")
    else:
        logger.info("Ion temperature data is not available.")

    if e_temp_data is not None:
        e_temp_data = e_temp_data.pipe(format_time).sort(right_on)
        events = events.join_asof(
            e_temp_data.collect(), left_on=left_on, right_on=right_on
        ).drop(right_on + "_right")
    else:
        logger.info("Electron temperature data is not available.")
    return events

# %% ../../notebooks/03_mag_plasma.ipynb 10
def update_events(
    events, plasma_data, plasma_meta, ion_temp_data, e_temp_data, **kwargs
):
    plasma_data = standardize_plasma_data(plasma_data, meta=plasma_meta)
    events = update_events_with_plasma_data(events, plasma_data, **kwargs)
    events = update_events_with_temp_data(events, ion_temp_data, e_temp_data)
    return events

# %% ../../notebooks/03_mag_plasma.ipynb 11
@deprecated(
    "Not used anymore, maybe outdated. Prefer to calculate the plasma parameters change separately"
)
def calc_plasma_parameter_change(
    df: pl.DataFrame,
    plasma_meta: PlasmaDataset = PlasmaDataset(),
):
    n_col = plasma_meta.density_col or DENSITY_COL
    n_before_col = f"{n_col}.before"
    n_after_col = f"{n_col}.after"

    if plasma_meta.temperature_col:
        col = plasma_meta.temperature_col
        df = df.with_columns(
            (pl.col(f"{col}.after") - pl.col(f"{col}.before")).alias(f"{col}.change")
        )

    if plasma_meta.speed_col:
        col = plasma_meta.speed_col
        df = df.with_columns(
            (pl.col("v.ion.after") - pl.col("v.ion.before")).alias("v.ion.change")
        )

    return (
        df.pipe(
            df_Alfven_speed,
            density=n_before_col,
            B="B.vec.before.l",
            col_name="v.Alfven.before.l",
            sign=True,
        )
        .pipe(
            df_Alfven_speed,
            density=n_after_col,
            B="B.vec.after.l",
            col_name="v.Alfven.after.l",
            sign=True,
        )
        .pipe(
            df_Alfven_speed,
            B=FIT_AMPL_COL,
            density=n_col,
            col_name="v.Alfven.change.l.fit",
            sign=False,
        )
        .with_columns(
            (pl.col(n_after_col) - pl.col(n_before_col)).alias("n.change"),
            (pl.col("v.ion.after.l") - pl.col("v.ion.before.l")).alias(
                "v.ion.change.l"
            ),
            (pl.col("B.after") - pl.col("B.before")).alias("B.change"),
            (pl.col("v.Alfven.after.l") - pl.col("v.Alfven.before.l")).alias(
                "v.Alfven.change.l"
            ),
        )
    )
