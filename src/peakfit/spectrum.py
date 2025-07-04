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


    def _register_backgroundresults(self, df: pd.DataFrame):
        """
        x
        y
        bg
        sig_est
        nit
        cost
        """
        self.background_result  = df
        self.data.update_y_bg(df.bg)
        return


    def _beads(self, params):

        if params["xclip_range"] is not None:
            _df_raw_clipped = cmn.xclip(self.xy_raw, params["xclip_range"])

        _df_extended = bg.extend_slope(
            xy          = _df_raw_clipped, 
            steepness   = params["steepness"], 
            lscale      = params["lscale"]
        )
        self.data.update_x(_df_extended.x)
        self.data.update_y_raw(_df_extended.y)
        _df_beads_result = bg.beads(xy=_df_extended)

        return _df_beads_result


    def fit_background(
        self, 
        params      : object,
        background  : callable,    # TODO like scipy.optimize functions.
        mode        : str       | None = None, 
    ):
        """
        mode: background type.
        params: parameters for background estimation.
        """

        if   mode == bg.BEADS:
            # params should have xrange, steepness and lscale.
            df_bgfitresult = self._beads(params)
            self.data.update_y_bg(df_bgfitresult["bg"])
        elif mode == bg.SHIRLEY:
            # params should have xrange.
            raise
        else:
            raise
        
        self._register_backgroundresults(df_bgfitresult)

        return df_bgfitresult


    def fit(
        self, 
        xrange  : tuple | None = None,  # TODO
        bg      : str   | None = None,  # TODO
    ):
        if self.fitparam is None:
            raise

        # Fitting #
        self.optimize_result = cmn.leastsq(
            xy          = None,
            model       = self.fitmodel,
            fitparam    = self.fitparam,
            x           = self.data.x,
            y           = self.data.y_raw,
        )

        if not self.optimize_result.success:
            print("ERROR")
            print(self.optimize_result)
            return

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
        _xy = cmn.xclip(xy=self.data.xy_all, range=range)
        return Spectrum(xy=_xy, fitparam=newfitparam)  # TODO: xySeries class
    

    def xshift(
        self,
        xshift      : float,
    ):
        self.data.x = self.data.x + xshift
        return self
    

    @classmethod
    def load_csv(cls, path: str):
        """
        Loading a csv file of xy_all data (already-fitted and exported).
        """
        return cls(xy=None, fitparam=None, path=path)

