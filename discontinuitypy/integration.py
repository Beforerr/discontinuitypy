# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/03_mag_plasma.ipynb.

# %% auto 0
__all__ = ['J_FACTOR', 'interpolate', 'interpolate2', 'format_time', 'combine_features', 'vector_project', 'vector_project_pl',
           'calc_rotation_angle_pl', 'compute_inertial_length', 'compute_Alfven_current',
           'calc_plasma_parameter_change', 'calc_combined_features']

# %% ../notebooks/03_mag_plasma.ipynb 1
import polars as pl
import polars.selectors as cs
from space_analysis.plasma.formulary import df_Alfven_speed as compute_Alfven_speed

# %% ../notebooks/03_mag_plasma.ipynb 2
def interpolate(
    df: pl.DataFrame, on="time", method="index", limit=1, limit_direction="both"
):
    # Note: limit is set to 1 to improve the confidence of the interpolation
    return pl.from_pandas(
        df.to_pandas()
        .set_index(on)
        .sort_index()
        .interpolate(
            method=method,
            limit=limit,
            limit_direction=limit_direction,
        )
        .reset_index()
    )


def interpolate2(df1: pl.DataFrame, df2, **kwargs):
    return pl.concat([df1, df2], how="diagonal_relaxed").pipe(interpolate, **kwargs)


def format_time(df: pl.DataFrame, time_unit="ns"):
    return df.with_columns(
        cs.datetime().dt.cast_time_unit(time_unit),
    )

# %% ../notebooks/03_mag_plasma.ipynb 3
from space_analysis.ds.meta import PlasmaMeta
from fastcore.all import concat


def combine_features(
    events: pl.DataFrame,
    states_data: pl.DataFrame,
    plasma_meta: PlasmaMeta = PlasmaMeta(),
    method: str = "interpolate",
):

    m = plasma_meta
    subset_cols = concat([m.density_col, m.velocity_cols, m.temperature_col])
    subset_cols = [item for item in subset_cols if item is not None]

    # change time format: see issue: https://github.com/pola-rs/polars/issues/12023
    time_unit = events["time"].dtype.time_unit
    states_data = states_data.sort("time").with_columns(
        pl.col("time").dt.cast_time_unit(time_unit)
    )
    events = events.sort("time")

    subset_cols = subset_cols + [
        "time"
    ]  # https://stackoverflow.com/questions/2347265/why-does-behave-unexpectedly-on-lists
    states_data_subset = states_data.select(subset_cols)
    df = events.join_asof(states_data, on="time", strategy="nearest")

    if method == "interpolate":
        before_df = interpolate2(
            df.select(time=pl.col("t.d_start")), states_data_subset
        )
        after_df = interpolate2(df.select(time=pl.col("t.d_end")), states_data_subset)
        return (
            df.sort("t.d_start")
            .join(
                before_df,
                left_on="t.d_start",
                right_on="time",
                suffix="_before",
            )
            .sort("t.d_end")
            .join(
                after_df,
                left_on="t.d_end",
                right_on="time",
                suffix="_after",
            )
        )

    elif method == "nearest":
        return (
            df.sort("t.d_start")
            .join_asof(
                states_data_subset,
                left_on="t.d_start",
                right_on="time",
                strategy="backward",
                suffix="_before",
            )
            .sort("t.d_end")
            .join_asof(
                states_data_subset,
                left_on="t.d_end",
                right_on="time",
                strategy="forward",
                suffix="_after",
            )
        )
    else:
        return df

# %% ../notebooks/03_mag_plasma.ipynb 5
import astropy.units as u
from astropy.constants import mu0, e
from plasmapy.formulary.lengths import inertial_length
from xarray_einstats import linalg
from .utils.basic import df2ts
from .core.propeties import calc_rotation_angle
import xarray as xr

# %% ../notebooks/03_mag_plasma.ipynb 6
def vector_project(v1: xr.DataArray, v2: xr.DataArray, dim="v_dim"):
    return xr.dot(v1, v2, dims=dim) / linalg.norm(v2, dims=dim)


def vector_project_pl(df: pl.DataFrame, v1_cols, v2_cols, name=None):
    v1 = df2ts(df, v1_cols).assign_coords(v_dim=["x", "y", "z"])
    v2 = df2ts(df, v2_cols).assign_coords(v_dim=["x", "y", "z"])
    result = vector_project(v1, v2, dim="v_dim")

    return df.with_columns(pl.Series(result.data).alias(name or "v_proj"))

# %% ../notebooks/03_mag_plasma.ipynb 8
def calc_rotation_angle_pl(df: pl.DataFrame, v1_cols, v2_cols, name):
    v1 = df.select(v1_cols).to_numpy()
    v2 = df.select(v2_cols).to_numpy()

    result = calc_rotation_angle(v1, v2)

    return df.with_columns(pl.Series(result).alias(name))

# %% ../notebooks/03_mag_plasma.ipynb 10
def compute_inertial_length(df: pl.DataFrame, density_col="plasma_density"):
    density = df[density_col].to_numpy() * u.cm ** (-3)
    result = inertial_length(density, "H+").to(u.km)

    return df.with_columns(ion_inertial_length=pl.Series(result.value))

# %% ../notebooks/03_mag_plasma.ipynb 12
def compute_Alfven_current(
    df: pl.DataFrame,
    density_col="plasma_density",
):
    Alfven_speed = df["Alfven_speed"].to_numpy() * u.km / u.s
    density = df[density_col].to_numpy() * u.cm ** (-3)

    result = (e.si * Alfven_speed * density).to(u.nA / u.m**2)

    return df.with_columns(j_Alfven=pl.Series(result.value))

# %% ../notebooks/03_mag_plasma.ipynb 14
from space_analysis.ds.meta import PlasmaMeta


def calc_plasma_parameter_change(
    df: pl.DataFrame,
    plasma_meta: PlasmaMeta = PlasmaMeta(),
):
    if plasma_meta.temperature_col:
        col = plasma_meta.temperature_col
        df = df.rename(
            {
                f"{col}_before": "T.before",
                f"{col}_after": "T.after",
            }
        ).with_columns((pl.col("T.after") - pl.col("T.before")).alias("T.change"))

    if plasma_meta.speed_col:
        col = plasma_meta.speed_col
        df = df.rename(
            {
                f"{col}_before": "v.ion.before",
                f"{col}_after": "v.ion.after",
            }
        ).with_columns(
            (pl.col("v.ion.after") - pl.col("v.ion.before")).alias("v.ion.change")
        )

    return (
        df.rename(
            {
                "plasma_density_before": "n.before",
                "plasma_density_after": "n.after",
            }
        )
        .pipe(
            compute_Alfven_speed,
            B="B.before",
            n="n.before",
            col_name="v.Alfven.before",
            sign=True,
        )
        .pipe(
            compute_Alfven_speed,
            B="B.after",
            n="n.after",
            col_name="v.Alfven.after",
            sign=True,
        )
        .pipe(
            compute_Alfven_speed,
            n="n.before",
            B="B.vec.before.l",
            col_name="v.Alfven.before.l",
            sign=True,
        )
        .pipe(
            compute_Alfven_speed,
            n="n.after",
            B="B.vec.after.l",
            col_name="v.Alfven.after.l",
            sign=True,
        )
        .with_columns(
            (pl.col("n.after") - pl.col("n.before")).alias("n.change"),
            (pl.col("v.ion.after.l") - pl.col("v.ion.before.l")).alias(
                "v.ion.change.l"
            ),
            (pl.col("B.after") - pl.col("B.before")).alias("B.change"),
            (pl.col("v.Alfven.after") - pl.col("v.Alfven.before")).alias(
                "v.Alfven.change"
            ),
            (pl.col("v.Alfven.after.l") - pl.col("v.Alfven.before.l")).alias(
                "v.Alfven.change.l"
            ),
        )
    )

# %% ../notebooks/03_mag_plasma.ipynb 15
from beforerr.polars import decompose_vector
from space_analysis.ds.meta import PlasmaMeta

J_FACTOR = ((u.nT / u.s) * (1 / mu0 / (u.km / u.s))).to(u.nA / u.m**2)


def calc_combined_features(
    df: pl.DataFrame,
    b_cols: list[str] = None,  # ["B_background_x", "B_background_y", "B_background_z"]
    detail: bool = True,
    normal_cols: list[str] = ["k_x", "k_y", "k_z"],
    Vl_cols=["Vl_x", "Vl_y", "Vl_z"],
    Vn_cols=["Vn_x", "Vn_y", "Vn_z"],
    thickness_cols=["L_k"],
    current_cols=["j0_k"],
    plasma_meta: PlasmaMeta = None,
    **kwargs,
):
    """Calculate the combined features of the discontinuity

    Args:
        df (pl.DataFrame): _description_
        normal_cols (list[str], optional): normal vector of the discontinuity plane. Defaults to [ "k_x", "k_y", "k_z", ].
        detail (bool, optional): _description_. Defaults to True.
        Vl_cols (list, optional): maxium variance direction vector of the magnetic field. Defaults to [ "Vl_x", "Vl_y", "Vl_z", ].
        Vn_cols (list, optional): minimum variance direction vector of the magnetic field. Defaults to [ "Vn_x", "Vn_y", "Vn_z", ].
        current_cols (list, optional): _description_. Defaults to ["j0_mn", "j0_k"].
    """

    length_norm = pl.col("ion_inertial_length")
    current_norm = pl.col("j_Alfven")
    b_norm = pl.col("b_mag")

    result = df

    if b_cols is not None:
        result = result.pipe(
            calc_rotation_angle_pl, b_cols, normal_cols, name="theta_n_b"
        )

    vec_cols = plasma_meta.velocity_cols
    density_col = plasma_meta.density_col

    result = (
        result.pipe(vector_project_pl, vec_cols, Vl_cols, name="v_l")
        .pipe(vector_project_pl, vec_cols, Vn_cols, name="v_n")
        .pipe(vector_project_pl, vec_cols, normal_cols, name="v_k")
        .with_columns(
            pl.col("v_n").abs(),
            pl.col("v_k").abs(),
            # v_mn=(pl.col("plasma_speed") ** 2 - pl.col("v_l") ** 2).sqrt(),
        )
        .with_columns(
            L_k=pl.col("v_k") * pl.col("duration"),
            j0_k=pl.col("d_star")
            / pl.col(
                "v_k"
            ),  # TODO: d_star corresponding to dB/dt, which direction is not exactly perpendicular to the k direction
            # NOTE: n direction is not properly determined for MVA analysis
            # j0_mn=pl.col("d_star") / pl.col("v_mn"),
            # L_n=pl.col("v_n") * pl.col("duration"),
            # L_mn=pl.col("v_mn") * pl.col("duration"),
            # NOTE: the duration is not properly determined for `max distance` method
            # L_k=pl.col("v_k") * pl.col("duration"),
        )
        .pipe(compute_inertial_length)
        .pipe(compute_Alfven_speed, n=density_col, B="b_mag")
        .pipe(compute_Alfven_current)
        .with_columns(
            cs.by_name(current_cols) * J_FACTOR.value,
        )
        .with_columns(
            (cs.by_name(thickness_cols) / length_norm).name.suffix("_norm"),
            (cs.by_name(current_cols) / current_norm).name.suffix("_norm"),
            (cs.by_name(b_cols) / b_norm).name.suffix("_norm"),
        )
    )

    if detail:
        result = (
            result.pipe(
                vector_project_pl,
                [_ + "_before" for _ in vec_cols],
                Vl_cols,
                name="v.ion.before.l",
            )
            .pipe(
                vector_project_pl,
                [_ + "_after" for _ in vec_cols],
                Vl_cols,
                name="v.ion.after.l",
            )
            .pipe(decompose_vector, "B.vec.before", suffixes=[".l", ".m", ".n"])
            .pipe(decompose_vector, "B.vec.after", suffixes=[".l", ".m", ".n"])
            .pipe(calc_plasma_parameter_change, plasma_meta=plasma_meta)
        )

    return result
