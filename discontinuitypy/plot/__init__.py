from datetime import datetime, timedelta
import pytplot
from discontinuitypy.utils.plot import ts_mva
from space_analysis.ds.tplot.formulary import ts_Alfven_speed
from space_analysis.ds.ts import set_ts_option
from space_analysis.ds.ts.plot import tsplot
from xarray import DataArray
import numpy as np


def to_datetime(date: np.datetime64):
    """
    Converts a numpy datetime64 object to a python datetime object
    """
    return date.astype("datetime64[ms]").astype(datetime)


def tsplot_Alvenicity(
    mag_da: DataArray,
    vec_da: DataArray,
    den_da: DataArray,
    start: datetime = None,
    end: datetime = None,
    offset=timedelta(seconds=0),
):
    """Plot the candidate event with velocity profiles"""
    start = start or to_datetime(mag_da.time.min().values)
    end = end or to_datetime(mag_da.time.max().values)

    trange = slice(start - offset, end + offset)

    mag_da = mag_da.sel(time=trange)
    vec_da = vec_da.sel(time=trange)
    den_da = den_da.sel(time=trange)

    mva_kwargs = dict(mva_data=mag_da, mva_tstart=start, mva_tstop=end)
    mag_mva_da = ts_mva(mag_da, **mva_kwargs)
    vec_mva_da = ts_mva(vec_da, **mva_kwargs)

    Bl_da = mag_mva_da.isel(v_dim=0)
    Alfven_l_da = ts_Alfven_speed(Bl_da, den_da)

    Vl_da = vec_mva_da.isel(v_dim=0).interp_like(Alfven_l_da)
    dVl_da = Vl_da - Vl_da.isel(time=abs(Alfven_l_da).argmin("time"))

    mag_mva_da = set_ts_option(mag_mva_da, type="B")
    vec_mva_da = set_ts_option(vec_mva_da, type="V")
    den_da = set_ts_option(den_da, type="n")
    Alfven_l_da.attrs["long_name"] = r"$V_{A,l}$"
    dVl_da.attrs["long_name"] = r"$dV_{i,l}$"

    layout = tsplot([mag_mva_da, vec_mva_da, [Alfven_l_da, dVl_da], den_da])
    layout[2].opts(ylabel=r"$V_l$ (km/s)")
    return layout


def tplot_Alvenicity(
    start,
    end,
    mag_tname: str,
    vec_tname: str,
    den_tname: str,
    offset=timedelta(seconds=0),
):
    """Plot the candidate event with velocity profiles"""
    mag_da = pytplot.data_quants[mag_tname]
    vec_da = pytplot.data_quants[vec_tname]
    den_da = pytplot.data_quants[den_tname]

    return tsplot_Alvenicity(
        mag_da, vec_da, den_da, start=start, end=end, offset=offset
    )
