# AUTOGENERATED! DO NOT EDIT! File to edit: ../../notebooks/utils/utils_r.ipynb.

# %% auto 0
__all__ = ['py2rpy_polars']

# %% ../../notebooks/utils/utils_r.ipynb 3
#| eval: false
import rpy2
import rpy2_arrow.arrow as pyra
from rpy2.robjects.packages import importr
import polars as pl

# %% ../../notebooks/utils/utils_r.ipynb 4
#| eval: false
def py2rpy_polars():
    "Helper functions to convert between `polars` and `R` dataframes"
    base = importr('base')

    conv_pl = rpy2.robjects.conversion.Converter(
        'Pandas to pyarrow',
        template=pyra.converter)

    @conv_pl.py2rpy.register(pl.DataFrame)
    def py2rpy_pandas(dataf: pl.DataFrame):
        pa_tbl = dataf.to_arrow()
        return base.as_data_frame(pa_tbl)
        # return pyra.converter.py2rpy(pa_tbl) # NOTE: not working for ggplot2

    conv_pl = rpy2.ipython.rmagic.converter + conv_pl
    return conv_pl
