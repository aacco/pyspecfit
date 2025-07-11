import peakfit
from .xyseries import xySeries
from . import common as cmn
from . import model as mdl
from . import background as bg
import pandas as pd
import matplotlib.pyplot as plt
import scipy
import scipy.optimize
import numpy as np

class Spectrum:
    """
    Data format to handle peak fitting components.

    Parameters
    ----------
    - self.data
    - self.fitparam
    - self.fitmodel
    - self.optimize_result
    - self.resultparam
    """

    XY = "xy"
    RESULTPARAM = "resultparam"
    CSV_EXT = ".csv"

    def __init__(
        self, 
        xy          : pd.DataFrame | None, 
        fitparam    : pd.DataFrame | None = None,
        path        : str          | None = None,
    ):
        if xy is not None:
            self.data       = xySeries(xy)

            if fitparam is None:
                self.fitparam   = None
                self.fitmodel   = None
            else:
                self.fitparam   = fitparam  # Maybe None.
                self.fitmodel   = cmn.fitmodeling(self.fitparam)

        elif path is not None:
            df              = pd.read_csv(path)
            self.data       = xySeries(df)
            self.fitparam   = None
            self.fitmodel   = None

        else:
            raise

        self.background_result  = None
    

    def set_fitparam(
        self,
        fitparam    : pd.DataFrame
    ):
        self.fitparam = fitparam
        return
    

    def _ndlist_to_serieslist(self, nds: list) -> list:
        rtn = []
        for nd in nds:
            rtn.append(pd.Series(nd))
        return rtn


    def _register_bg_results(self, df: pd.DataFrame):
        self.background_result  = df

        if "x" in df.columns:
            self.data.update_x(df["x"])

        if "y" in df.columns:
            self.data.update_y_raw(df["y"])

        self.data.update_y_bg(df["bg"])
        return


    def fit_background(
        self, 
        func        : callable,
        xy          = None,
        args        = (),
        kwargs      = {},
    ):
        """
        Parameters
        ----------
        func : callable
            Function which computes the vector backgrounds 
            with the signature ``func(xy, *args, **kwargs)``.
            The return value of `func` must include a `bg` attribute
            as results.
        
        xy : pandas.DataFrame, optional
            DataFrame of xy for background fitting. If None (default),
            the value is `self.data.xy_raw`.

        args, kwargs : tuple and dict, optional
            Additional arguments passed to `func`. Both empty by default.
        """

        if xy is None:
            xy_passing = pd.DataFrame({"x": self.data.x, "y": self.data.y_raw})
        else:
            xy_passing = xy

        bg_result = func(xy_passing, *args, **kwargs)

        self._register_bg_results(bg_result)

        return bg_result


    def fit(
        self, 
        xrange      : tuple         | None = None,  # TODO
        bg          : str           | None = None,  # TODO
        fitparam    : pd.DataFrame  | None = None,
    ):
        if self.fitparam is None:
            raise

        if self.data.has_bg():
            y_for_fit = self.data.y_raw_without_bg
        else:
            y_for_fit = self.data.y_raw

        xy_for_fit = pd.DataFrame({"x": self.data.x, "y": y_for_fit})

        if xrange is not None:
            xy_for_fit = cmn.xclip(xy_for_fit, xrange, reset_index=False)

        # Fitting #
        self.optimize_result = cmn.leastsq(
            xy          = xy_for_fit,
            model       = self.fitmodel,
            fitparam    = self.fitparam,
            #x           = self.data.x,
            #y           = y_for_fit,
        )

        if not self.optimize_result.success:
            print("ERROR")
            print(self.optimize_result)
            raise

        self._register_fitresults()

        return
    

    def _register_fitresults(self):
        """
        Update elements of Spectrum instance on fit results.
        """
        # Parameter setting #
        self.resultparam = cmn.convert_fitresult_to_df(
            fitresult   = self.optimize_result, 
            fitparam    = self.fitparam
        )

        y_fit  = self.fitmodel(
            x           = self.data.x.to_numpy(), 
            args        = self.optimize_result.x
        )
        self.data.update_y_fit(y_fit)

        xy_eles = cmn.build_peak_elements(
            x           = self.data.x.values, 
            fitresult   = self.optimize_result, 
            fitparam    = self.fitparam
        )
        
        # y-axis data by eliminating "x" column 
        # (= screening by "peak_name" column) from xy_eles.
        self.element_peaknames      = self.fitparam["peak_name"]
        self.data.update_y_eles(xy_eles[self.element_peaknames])

        # Calculation on peak parameters #
        self.resultparam['FWHM']    = cmn.series_fwhm(self.resultparam)
        self.resultparam['area']    = cmn.series_area(self.data.xy_eles)
        
        return


    def print_resultparam(self):
        print(self.resultparam.drop(columns=["display_name"]))
        return


    def xclip(
        self,
        range       : tuple,
        newfitparam : pd.DataFrame | None = None
    ):
        """
        Roughly clipping xy data by x-axis range.
        
        - xy    : pd.Dataframe like including "x" and "y" columns.
        - range : Tuple object as (begin, end).
        """
        _xy = cmn.xclip(xy=self.data.xy_all, range=range)

        return Spectrum(xy=_xy, fitparam=newfitparam)  # TODO: xySeries class
    

    def xshift(
        self,
        shift      : float,
    ):
        self.data.xshift(shift)
        return self
    

    @classmethod
    def load_csv(cls, path: str):
        """
        Loading a csv file of xy_all data (already-fitted and exported).
        """
        return cls(xy=None, fitparam=None, path=path)

