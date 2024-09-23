# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/detection/01_variance.ipynb.

# %% auto 0
__all__ = ['INDEX_STD_THRESHOLD', 'INDEX_FLUC_THRESHOLD', 'INDEX_DIFF_THRESHOLD', 'SPARSE_THRESHOLD', 'compute_std',
           'add_neighbor_std', 'compute_index_std', 'compute_combinded_std', 'compute_index_fluctuation', 'pl_dvec',
           'compute_index_diff', 'compute_indices', 'filter_indices']

# %% ../../notebooks/detection/01_variance.ipynb 3
import polars as pl
import polars.selectors as cs
from datetime import timedelta
from beforerr.polars import pl_norm, format_time
from ..utils.basic import _expand_selectors

# %% ../../notebooks/detection/01_variance.ipynb 4
def compute_std(
    df: pl.LazyFrame,
    period: timedelta,  # period to group by
    index_column="time",
    cols: list[str] = ["BX", "BY", "BZ"],
    every: timedelta = None,  # every to group by (default: period / 2)
    result_column="std",
):
    every = every or period / 2

    std_cols = [col_name + "_std" for col_name in cols]

    std_df = (
        df.group_by_dynamic(index_column, every=every, period=period)
        .agg(
            pl.len(),
            pl.col(cols).std(ddof=0).name.suffix("_std"),
        )
        .with_columns(
            pl_norm(std_cols).alias(result_column),
        )
        .drop(std_cols)
    )
    return std_df

# %% ../../notebooks/detection/01_variance.ipynb 5
def add_neighbor_std(
    df: pl.LazyFrame,
    tau: timedelta,
    join_strategy="inner",
    std_column="std",
    time_column="time",
):
    """
    Get the neighbor standard deviations

    Parameters
    ----------
    - df (pl.LazyFrame): The input DataFrame.
    - tau : The time interval value.

    Notes
    -----
    Simply shift would not work correctly if data is missing, like `std_next = pl.col("B_std").shift(-2)`.

    """

    # Calculate the standard deviation index
    prev_std_df = df.select(
        pl.col(time_column) + tau,
        cs.by_name(std_column, "len").name.suffix("_prev"),
    ).pipe(format_time)

    next_std_df = df.select(
        pl.col(time_column) - tau,
        cs.by_name(std_column, "len").name.suffix("_next"),
    ).pipe(format_time)

    return df.join(prev_std_df, on=time_column, how=join_strategy).join(
        next_std_df, on=time_column, how=join_strategy
    )

# %% ../../notebooks/detection/01_variance.ipynb 6
def compute_index_std(
    df: pl.LazyFrame,
    std_column="std",
):
    """
    Compute the standard deviation index based on the given DataFrame

    Parameters
    ----------
    - df (pl.LazyFrame): The input DataFrame.

    Returns
    -------
    - pl.LazyFrame: DataFrame with calculated 'index_std' column.

    Examples
    --------
    >>> index_std_df = compute_index_std_pl(df)
    >>> index_std_df
    """

    return df.with_columns(
        index_std=pl.col(std_column)
        / pl.max_horizontal(f"{std_column}_prev", f"{std_column}_next"),
    )

# %% ../../notebooks/detection/01_variance.ipynb 8
def compute_combinded_std(
    df: pl.LazyFrame,
    cols: list[str],
    every: timedelta,  # every to group by (default: period / 2)
    period: timedelta = None,  # period to group by
    index_column="time",
    result_column="std_combined",
):
    prev_df = df.with_columns(pl.col(index_column) + period)
    next_df = df.with_columns(pl.col(index_column) - period)
    return (
        pl.concat([prev_df, next_df])
        .sort(index_column)
        .group_by_dynamic(index_column, every=every, period=period)
        .agg(cs.by_name(cols).std(ddof=0).name.suffix("_combined"))
        .select(
            index_column,
            pl_norm([col_name + "_combined" for col_name in cols]).alias(result_column),
        )
        .pipe(format_time)
    )


# | export
def compute_index_fluctuation(df: pl.LazyFrame, std_column="std", clean=True):
    std_combined = pl.col(f"{std_column}_combined")
    std_added = pl.sum_horizontal(f"{std_column}_prev", f"{std_column}_next")

    index_df = df.with_columns(index_fluctuation=std_combined / std_added)
    return index_df.drop(f"{std_column}_combined") if clean else index_df

# %% ../../notebooks/detection/01_variance.ipynb 10
def pl_dvec(columns, *more_columns):
    all_columns = _expand_selectors(columns, *more_columns)
    return [
        (pl.col(column).first() - pl.col(column).last()).alias(f"d{column}_vec")
        for column in all_columns
    ]

# %% ../../notebooks/detection/01_variance.ipynb 11
def compute_index_diff(
    df: pl.LazyFrame,
    every: timedelta,
    cols: list[str],
    period: timedelta = None,
    clean=True,
):
    db_cols = ["d" + col + "_vec" for col in cols]

    index_diff = (
        df.with_columns(pl_norm(cols).alias("_vec_mag"))
        .group_by_dynamic("time", every=every, period=period)
        .agg(
            pl.col("_vec_mag").mean().name.suffix("_mean"),
            *pl_dvec(cols),
        )
        .with_columns(pl_norm(db_cols).alias("_dvec_mag"))
        .with_columns(index_diff=pl.col("_dvec_mag") / pl.col("_vec_mag_mean"))
    )

    if clean:
        return index_diff.drop("_vec_mag_mean", "_dvec_mag", *db_cols)
    else:
        return index_diff

# %% ../../notebooks/detection/01_variance.ipynb 12
def compute_indices(
    df: pl.LazyFrame,
    tau: timedelta,
    cols: list[str],
    clean=True,
    join_strategy="inner",
    on="time",
) -> pl.LazyFrame:
    """
    Compute all index based on the given DataFrame and tau value.

    Parameters
    ----------
    df : pl.DataFrame
        Input DataFrame.
    tau : datetime.timedelta
        Time interval value.
    cols : list
        List of column names.

    Returns
    -------
    tuple :
        Tuple containing DataFrame results for fluctuation index,
        standard deviation index, and 'index_num'.

    Examples
    --------
    >>> indices = compute_indices(df, tau)

    Notes
    -----
    - This is a wrapper for `_compute_indices` with `pl.LazyFrame` input.
    - Simply shift to calculate index_std would not work correctly if data is missing,
        like `std_next = pl.col("B_std").shift(-2)`.
    - Drop null though may lose some IDs (using the default `join_strategy`).
        Because we could not tell if it is a real ID or just a partial wave
        from incomplete data without previous or/and next std.
        Hopefully we can pick up the lost ones with smaller tau.
    - TODO: Can be optimized further, but this is already fast enough.
        - TEST: if `join` can be improved by shift after filling the missing values.
        - TEST: if `list` in `polars` really fast?
    """

    every = tau / 2
    period = tau

    df = df.pipe(format_time).sort(on)

    stds_df = df.pipe(compute_std, period=period, cols=cols).pipe(
        add_neighbor_std, tau=tau
    )

    combined_std_df = compute_combinded_std(df, cols, every=every, period=period)

    indices = (
        df.pipe(compute_index_diff, every=every, period=period, cols=cols)
        .join(stds_df, on=on)
        .join(combined_std_df, on=on, how=join_strategy)
        .pipe(compute_index_std)
        .pipe(compute_index_fluctuation, clean=clean)
    )

    if clean:
        return indices.drop(["std_prev", "std_next"])
    else:
        return indices

# %% ../../notebooks/detection/01_variance.ipynb 14
INDEX_STD_THRESHOLD = 2
INDEX_FLUC_THRESHOLD = 1
INDEX_DIFF_THRESHOLD = 0.1
SPARSE_THRESHOLD = 15

# %% ../../notebooks/detection/01_variance.ipynb 15
def filter_indices(
    df: pl.LazyFrame,
    index_std_threshold: float = INDEX_STD_THRESHOLD,
    index_fluc_threshold: float = INDEX_FLUC_THRESHOLD,
    index_diff_threshold: float = INDEX_DIFF_THRESHOLD,
    sparse_num: int = SPARSE_THRESHOLD,
) -> pl.LazyFrame:
    # filter indices to get possible IDs

    return df.filter(
        pl.col("index_std") > index_std_threshold,
        pl.col("index_fluctuation") > index_fluc_threshold,
        pl.col("index_diff") > index_diff_threshold,
        pl.col(
            "index_std"
        ).is_finite(),  # for cases where neighboring groups have std=0
        pl.col("len") > sparse_num,
        pl.col("len_prev")
        > sparse_num,  # filter out sparse intervals, which may give unreasonable results.
        pl.col("len_next")
        > sparse_num,  # filter out sparse intervals, which may give unreasonable results.
    ).drop(["len_prev", "len_next"])
