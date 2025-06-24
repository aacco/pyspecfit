import peakfit
from . import common as cmn
from . import model as mdl
import pandas as pd
import matplotlib.pyplot as plt
import peakfit.peak
import scipy
import scipy.optimize
import numpy as np

class Spectrum:
    """
    Data format to handle peak fitting components.

    Parameters
    ----------
    - self.xy_all
    - self.x
    - self.y_raw
    - self.y_bg
    - self.y_fit
    - self.xy_eles
    - self.y_eles  # y-axis extraction from self.xy_eles.
    - self.element_peaknames
    (- self.elementpeaks_names?)

    -------
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
        xy:         pd.DataFrame | None, 
        fitparam:   pd.DataFrame | None,
        path:       str | None = None,
    ):
        if xy is not None and fitparam is not None:
            self.xy_all     = None
            self.xy_raw     = xy
            self.x          = xy["x"]
            self.y_raw      = xy["y"]
            self.y_fit      = None
            self.y_bg       = None
            self.xy_eles    = None
            self.y_eles     = None
            self.fitparam   = fitparam
            self.fitmodel   = cmn.fitmodeling(self.fitparam)

        elif path is not None:
            self.xy_all     = pd.read_csv(path)
            self.xy_raw     = None
            self.x          = self.xy_all["x"]
            self.y_raw      = self.xy_all["y_raw"]
            self.y_fit      = self.xy_all["y_fit"]
            self.y_bg       = self.xy_all["y_bg"]
            self.xy_eles    = self.xy_all.drop(columns=["y_raw", "y_fit", "y_bg"])
            self.y_eles     = self.xy_all.drop(columns=["x", "y_raw", "y_fit", "y_bg"])
            self.fitparam   = None
            self.fitmodel   = None
        else:
            raise
    

    #def read_raw(path: str, mode):
    #    pass
    
    def _ndlist_to_serieslist(self, nds: list) -> list:
        rtn = []
        for nd in nds:
            rtn.append(pd.Series(nd))
        return rtn


    def fit(self, bg=None):  # TODO: BG
        # Fitting #
        self.optimize_result = cmn.leastsq(
            xy          = self.xy_raw,
            model       = self.fitmodel,
            fitparam    = self.fitparam
        )

        self._update_elements()
        return
    
    def _update_elements(self):
        # Parameter setting #
        self.resultparam = cmn.convert_fitresult_to_df(
            fitresult   = self.optimize_result, 
            fitparam    = self.fitparam
        )
        self.y_fit  = self.fitmodel(
            x           = self.x.to_numpy(), 
            args        = self.optimize_result.x
        )
        self.xy_eles = cmn.build_peak_elements(
            x           = self.x.values, 
            fitresult   = self.optimize_result, 
            fitparam    = self.fitparam
        )
        
        # y-axis data by eliminating "x" column (= screening by "peak_name" column) from xy_eles.
        self.element_peaknames      = self.fitparam["peak_name"]
        self.y_eles                 = self.xy_eles[self.element_peaknames]

        # Build up xy_all #
        _xy_all_list = [self.x, self.y_raw, self.y_bg, self.y_fit]
        xy_all_list = self._ndlist_to_serieslist(_xy_all_list)
        xy_all_list.append(self.y_eles)
        _new_column_list = ["x", "y_raw", "y_bg", "y_fit"]  # Except for elemental peaks.
        new_column_list = _new_column_list + self.element_peaknames.tolist()
        self.xy_all                 = pd.concat(xy_all_list, axis="columns")
        self.xy_all.columns         = new_column_list

        # Calculation on peak parameters #
        self.resultparam['FWHM']    = cmn.series_fwhm(self.resultparam)
        self.resultparam['area']    = cmn.series_area(self.xy_eles)
        
        return

    def print_resultparam(self):
        print(self.resultparam.drop(columns=["display_name"]))
        return

    #def save_csvs(self, dir: str):
    #    path_xy = dir + "/" + XY + CSV_EXT
    #    self.xy_all.to_csv(path_xy)
    #
    #    path_res = dir + "/" + RESULTPARAM + CSV_EXT
    #    self.resultparam.to_csv(path_res)
    #    return
    
    @classmethod
    def load_csv(cls, path: str):
        """
        Loading xy_all data (already-fitted and exported).
        """
        return cls(xy=None, fitparam=None, path=path)

