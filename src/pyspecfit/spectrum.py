from .xyseries import xySeries
from .bgseries import bgSeries
from . import common as cmn
import pandas as pd
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
        x           : pd.Series    | np.ndarray | None = None,  # x-axis data.
        raw         : pd.Series    | np.ndarray | None = None,  # y-axis raw data.
        xy          : pd.DataFrame              | None = None,  # combination of x and raw as DataFrame.
        sanitized   : bool                             = False,
        fitparam    : pd.DataFrame              | None = None,
        loadpath    : str                       | None = None,
    ):
        if xy is not None:
            if sanitized:
                self.data = xySeries(loaded_data=xy)
            else:
                cols = []
                for col in xy.columns:
                    cols.append(col)
                self.data       = xySeries(x=xy[cols[0]], raw=xy[cols[1]])

        elif x is not None and raw is not None:
            self.data       = xySeries(x=x, raw=raw)

        # For loaded data.
        elif loadpath is not None:
            df             = pd.read_csv(loadpath, header=[0, 1])  # With multi-columns.

            # Drop columns whose names contain "Unnamed" (case-insensitive)
            #df              = _df.loc[:, ~_df.columns.str.contains('^Unnamed', case=False)]
            self.data       = xySeries(loaded_data=df)

        else:
            raise

        if fitparam is None:
            self.fitparam   = None
            self.fitmodel   = None
        else:
            self.set_fitparam(fitparam)
            self.fitmodel   = cmn.fitmodeling(self.fitparam)

        self.background_result  = None
    

    def set_fitparam(
        self,
        fitparam    : pd.DataFrame
    ):
        used_fitparam = fitparam[fitparam["is_used"] == True]
        self.fitparam = used_fitparam
        return
    

    def _ndlist_to_serieslist(self, nds: list) -> list:
        rtn = []
        for nd in nds:
            rtn.append(pd.Series(nd))
        return rtn


    def _register_bg_results(
        self, 
        bgser   : bgSeries, 
        bg_name : str,
    ):
        self.background_result  = bgser

        # TODO: refactoring.
        # If returned value contains "x" attribute, update x-axis.
        #if bgser.has_new_x:
        #    self.data.update_x(bgser.new_x)

        #if bgser.has_new_y:
        #    self.data.update_raw(bgser.new_y)

        self.data.update_bg_element(ser=bgser.bg, column_name=bg_name)
        return


    def fit_background(
        self, 
        func        : callable,
        bg_name     = None,
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
            xy_passed = pd.DataFrame({"x": self.data.x, "y": self.data.y_raw})
        else:
            xy_passed = xy

        # Background fitting #
        bg_result = func(xy_passed, *args, **kwargs)

        # Register background results #
        self._register_bg_results(bg_result, bg_name)

        return bg_result
    
    # TODO
    #def background_estimation(
    #    self,
    #    func        : callable     | list,
    #    bg_name     : str          | list,
    #    xy          : pd.DataFrame        | None = None,
    #    args        = (),
    #    kwargs      = {},
    #):
    #    """
    #    Wrapper for `fit_background` method.
    #    """
    #    #return self.fit_background(
    #    #    func    = func,
    #    #    bg_name = bg_type,
    #    #    xy      = xy,
    #    #    args    = args,
    #    #    kwargs  = kwargs,
    #    #)
    #    return # TODO


    def fit(
        self, 
        xrange      : tuple         | None = None,  # TODO
        fitparam    : pd.DataFrame  | None = None,
    ):
        if fitparam is not None:
            self.set_fitparam(fitparam)
        if self.fitparam is None:
            raise

        # "y_for_fit" must have no background component.
        if self.data.has_bg():
            print("Has bg!")
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

        if self.optimize_result.success:
            print("Fitting succeeded.")
            print(self.optimize_result)

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

        y_fit_wo_bg  = self.fitmodel(
            x           = self.data.x.to_numpy(), 
            args        = self.optimize_result.x
        )

        #
        # Update y_fit including background component.
        # "y_fit" data out of the fitting range will be NaN 
        # because sum of any value and NaN will be NaN.
        #
        self.data.update_y_fit(y_fit_wo_bg + self.data.y_bg)

        xy_eles = cmn.build_peak_elements(
            x           = self.data.x.values, 
            fitresult   = self.optimize_result, 
            fitparam    = self.fitparam
        )
        
        #
        # y-axis data by eliminating "x" column 
        # (= screening by "peak_name" column) from xy_eles.
        #
        self.element_peaknames      = self.fitparam["peak_name"]
        for col in self.element_peaknames:
            self.data.update_peak_element(ser=xy_eles[col], column_name=col)

        #
        # Calculation on peak parameters #
        #
        self.resultparam['FWHM']    = cmn.series_fwhm(self.resultparam)
        self.resultparam['area']    = cmn.series_area(x=self.data.x, peaks=self.data.peaks)
        
        return


    def print_resultparam(self):
        print(self.resultparam.drop(columns=["display_name"]))
        #print(self.data.all)
        return


    #def xclip(
    #    self,
    #    range       : tuple,
    #    newfitparam : pd.DataFrame | None = None
    #):
    #    """
    #    Roughly clipping xy data by x-axis range.
    #    
    #    - xy    : pd.Dataframe like including "x" and "y" columns.
    #    - range : Tuple object as (begin, end).
    #    """
    #    _xy = cmn.xclip(xy=self.data.xy_all, range=range)

    #    return Spectrum(xy=_xy, fitparam=newfitparam)  # TODO: xySeries class

    def xclip(
        self,
        clip_range  : tuple, 
        reset_index                       = True,
        newfitparam : pd.DataFrame | None = None,
    ):
        """
        Roughly clipping xy data by x-axis range.
        - xy    : pd.Dataframe like including "x" and "y" columns.
        - range : Tuple object as (begin, end).
        """
        xy = self.data.all
        x = xy["base", "x"]

        if cmn.is_descending(xy["base"]):
            i_x_min = cmn.x_to_index(clip_range[1], x)
            i_x_max = cmn.x_to_index(clip_range[0], x)
        else:
            i_x_min = cmn.x_to_index(clip_range[0], x)
            i_x_max = cmn.x_to_index(clip_range[1], x)

        xy_rtn = xy.loc[ i_x_min : i_x_max ]

        if reset_index:
            xy_rtn = xy_rtn.reset_index(drop = True)
        #print(f"xy_rtn: {xy_rtn}")

        return Spectrum(xy=xy_rtn, sanitized=True, fitparam=newfitparam)
    

    def xshift(
        self,
        shift      : float, # shift value
    ):
        self.data.xshift(shift)
        return self
    

    @classmethod
    def load_csv(cls, path: str):
        """
        Loading a csv file of xy_all data (already-fitted and exported).
        """
        return cls(xy=None, fitparam=None, loadpath=path)

    # Bypass for self.data properties.
    @property
    def xy_all(self):
        return self.data.xy_all

    @property
    def all(self):
        """Short for xy_all"""
        return self.data.xy_all

    #@property
    #def xy_raw(self):
    #    return self.data.xy_raw

    #@property
    #def raw(self):
    #    """
    #    Shortcut for xy_raw
    #    """
    #    return self.data.xy_raw

    @property
    def x(self):
        return self.data.x

    @property
    def y_raw(self):
        return self.data.y_raw

    @property
    def y(self):
        """
        Shortcut for `y_raw`.
        """
        return self.data.y_raw

    @property
    def y_bg(self):
        return self.data.y_bg

    @property
    def y_raw_without_bg(self) -> pd.Series:
        return self.data.y_raw_without_bg

    @property
    def y_fit(self):
        return self.data.y_fit

    #@property
    #def xy_eles(self):
    #    return self.data.xy_eles

    @property
    def y_eles(self):
        return self.data.y_eles

    @property
    def columns(self):
        return self.data.columns

    @property
    def columns_elements(self):
        return self.data.columns_peaks

    @property
    def columns_peaks(self):
        return self.data.columns_peaks

    @property
    def residual(self) -> pd.Series:
        return self.data.residual
    
    @property
    def rms(self):
        """
        Root mean squared errors.
        """
        r = self.data.residual
        rms = np.sqrt( ( r**2 ).mean() )
        return np.round(rms, 4)

    def data_to_df(self):
        return self.data.to_df()
    
    def has_bg(self):
        return self.data.has_bg()

    def save_data(self, path):
        """
        Wrapper for `pandas.DataFrame.to_csv` with `index=False`.
        """
        self.all.to_csv(path_or_buf=path, index=False)
        return 
