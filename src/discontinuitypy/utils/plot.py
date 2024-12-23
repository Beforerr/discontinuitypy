# AUTOGENERATED! DO NOT EDIT! File to edit: ../../../notebooks/utils/01_plotting.ipynb.

# %% auto 0
__all__ = ['time_stamp', 'setup_mva_tplot_base', 'ts_mva', 'setup_mva_plot', 'set_mva_tname_option', 'plot_candidate',
           'plot_event', 'plot_candidates']

# %% ../../../notebooks/utils/01_plotting.ipynb 0
import xarray as xr
import pandas as pd
from datetime import datetime

from pyspedas import tvector_rotate, minvar_matrix_make, tvectot, deriv_data

import pytplot
from pytplot import tplot, split_vec
from pytplot import timebar, degap, options
from space_analysis.ds.tplot import store_data

from matplotlib.pyplot import Axes

from ..datasets import IDsDataset
from loguru import logger

# %% ../../../notebooks/utils/01_plotting.ipynb 2
def time_stamp(ts):
    "Return POSIX timestamp as float."
    return pd.Timestamp(ts, tz="UTC").timestamp()

# %% ../../../notebooks/utils/01_plotting.ipynb 3
def setup_mva_tplot_base(
    tname: str,
    mva_tname: str,
    mva_tstart: datetime = None,
    mva_tstop: datetime = None,
    calc_magnitude=True,
):
    mva_mat = minvar_matrix_make(
        mva_tname, tstart=str(mva_tstart), tstop=str(mva_tstop)
    )[0]
    tvar = tvector_rotate(mva_mat, tname)[0]
    if calc_magnitude:
        return tvectot(tvar, join_component=True)
    return tvar


# TODO: refactor (to remove pytplot.store_data steps)
def ts_mva(
    data: xr.DataArray,
    mva_data: xr.DataArray,
    **kwargs,
):
    data_tname = store_data(data.rename(f"{data.name}_temp"))
    mva_tname = store_data(mva_data.rename("mva_data_temp"))
    tvar = setup_mva_tplot_base(data_tname, mva_tname, **kwargs)

    ts = pytplot.data_quants[tvar]

    pytplot.del_data(data_tname)
    pytplot.del_data(mva_tname)
    pytplot.del_data(tvar)

    return ts

# %% ../../../notebooks/utils/01_plotting.ipynb 4
def setup_mva_plot(
    data: xr.DataArray,
    tstart: datetime,
    tstop: datetime,
    mva_tstart: datetime = None,
    mva_tstop: datetime = None,
):
    mva_tstart = mva_tstart or tstart
    mva_tstop = mva_tstop or tstop

    mva_b = data.sel(time=slice(mva_tstart, mva_tstop))
    temp_b = data.sel(time=slice(tstart, tstop))
    ts_mva_b = ts_mva(temp_b, mva_b, mva_tstart=mva_tstart, mva_tstop=mva_tstop)
    tvar2plot = store_data(ts_mva_b)

    set_mva_tname_option(tvar2plot, type="B")
    degap(tvar2plot)
    return tvar2plot


def set_mva_tname_option(
    tname,
    type="B",
):
    options_dict = {
        "B": {
            "title": "$B$",
            "subtitle": "[nT LMN]",
            "legend_names": [r"$B_l$", r"$B_m$", r"$B_n$", r"$B_{total}$"],
        },
        "V": {
            "title": "$V$",
            "subtitle": "[km/s LMN]",
            "legend_names": [r"$V_l$", r"$V_m$", r"$V_n$", r"$V_{total}$"],
        },
    }

    if type in options_dict:
        type_options = options_dict[type]
        options(tname, "ytitle", type_options["title"])
        options(tname, "ysubtitle", type_options["subtitle"])
        options(tname, "legend_names", type_options["legend_names"])

# %% ../../../notebooks/utils/01_plotting.ipynb 5
def format_candidate_title(candidate: dict):
    def format_float(x):
        return rf"$\bf {x:.2f} $" if isinstance(x, (float, int)) else rf"$\bf {x} $"

    base_line = rf'$\bf {candidate.get("type", "N/A")} $ candidate (time: {candidate.get("time", "N/A")}) with index '
    index_line = rf'i1: {format_float(candidate.get("index_std", "N/A"))}, i2: {format_float(candidate.get("index_fluctuation", "N/A"))}, i3: {format_float(candidate.get("index_diff", "N/A"))}'
    info_line = rf'$B_n/B$: {format_float(candidate.get("BnOverB", "N/A"))}, $dB/B$: {format_float(candidate.get("dBOverB", "N/A"))}, $(dB/B)_{{max}}$: {format_float(candidate.get("dBOverB_max", "N/A"))},  $Q_{{mva}}$: {format_float(candidate.get("Q_mva", "N/A"))}'
    title = rf"""{base_line}
    {index_line}
    {info_line}"""
    return title

# %% ../../../notebooks/utils/01_plotting.ipynb 6
def plot_candidate(
    event: dict,
    data: xr.DataArray,
    add_ids_properties=True,
    plot_current_density=False,
    plot_fit_data=False,
    add_timebars=True,
    add_plasma_params=False,
    **kwargs,
):
    if pd.notnull(event.get("t_us")) and pd.notnull(event.get("t_ds")):
        tvar = setup_mva_plot(
            data,
            event["tstart"],
            event["tstop"],
            event["t_us"],
            event["t_ds"],
        )
    else:
        tvar = setup_mva_plot(data, event["tstart"], event["tstop"])

    tvars2plot = [tvar]

    if plot_current_density:
        Bl = split_vec(tvar)[0]
        dBldt = deriv_data(Bl)[0]
        # v_k = event.get("v_k")
        # pytplot.data_quants[dBldt] = pytplot.data_quants[dBldt] / v_k * J_FACTOR.value #TODO: fix this
        tvars2plot.append(dBldt)

        options(dBldt, "ytitle", "$J$")
        options(dBldt, "ysubtitle", "[nA/m$^2$]")
        options(dBldt, "legend_names", "$J_m$")

    if add_timebars:
        d_time = event.get("t.d_time")
        d_start = event.get("t_us")
        d_stop = event.get("t_ds")

        if d_time:
            timebar(time_stamp(d_time), color="red")
        if d_start and pd.notnull(d_start):
            timebar(time_stamp(d_start))
        if d_stop and pd.notnull(d_stop):
            timebar(time_stamp(d_stop))

    title = ""

    if add_ids_properties:
        thickness = event.get("L_k")
        current_density = event.get("j0_k")
        title += "#Discontinuity properties# "
        if thickness:
            title += rf"$L: {thickness:.2f} \mathrm{{km}}$"
        if current_density:
            title += rf", $j: {current_density:.2f} \mathrm{{nA/m}}^2$"

    if add_plasma_params:
        plasma_speed = event.get("plasma_speed")
        plasma_density = event.get("plasma_density")
        plasma_temperature = event.get("plasma_temperature")

        title += "\n#Plasma parameters# "
        if plasma_speed:
            title += rf"$V_i: {plasma_speed:.2f} \mathrm{{km/s}}$"
        if plasma_density:
            title += rf", $n_i: {plasma_density:.2f} \mathrm{{cm}}^{{-3}}$"
        if plasma_temperature:
            title += rf", $T_i: {plasma_temperature:.2f} \mathrm{{eV}}$"

        # options(tvar, "title", title)

    for tvar2plot in tvars2plot:
        options(tvar2plot, "thick", 2)
        options(tvar2plot, "char_size", 16)

    fig, axes = tplot(tvars2plot, return_plot_objects=True)
    if isinstance(axes, Axes):
        axes = [axes]

    base_axis = axes[0]

    if plot_fit_data:
        fit_data = event.get("fit.best_fit")
        fit_time = event.get("fit.time")

        c = event.get("fit.vars.c")
        amp = event.get("fit.vars.amplitude")
        sigma = event.get("fit.vars.sigma")

        d_star = event.get("d_star")
        rsquared = event.get("fit.stat.rsquared")
        chisqr = event.get("fit.stat.chisqr")

        base_axis.plot(d_time, c + amp / 2, marker="o", markersize=10, color="red")
        if fit_time is not None and fit_data is not None:
            base_axis.plot(
                fit_time, fit_data, label="Fit", color="black", linestyle="--"
            )

        title += f"\n#Fit# $\max dB/dt$: {d_star:.2f}, $R^2$: {rsquared:.2f}, $\chi^2$: {chisqr:.2f}"
        title += f"\n#Fit# $c$: {c:.2f}, $Amp$: {amp:.2f}, $\Sigma$: {sigma:.2f}"

    # add title to the first plot
    base_axis.set_title(title)

    return fig, axes

# %% ../../../notebooks/utils/01_plotting.ipynb 7
def plot_event(self: IDsDataset, event=None, index=None, **kwargs):
    if event is None:
        event = self.get_event(index)
    data = self.get_event_data(event, **kwargs)
    return plot_candidate(event, data, **kwargs)


def plot_candidates(
    self: IDsDataset, indices=None, num=4, random=True, predicate=None, **kwargs
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

    return [plot_event(self, index=i, **kwargs) for i in indices]
