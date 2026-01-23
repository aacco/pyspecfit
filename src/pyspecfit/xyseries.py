import numpy as np
import pandas as pd

class xySeries:
    """
    "xySeries" is a wrapper class of pandas.DataFrame
    and provides a base structure of "Spectrum class".

    - self.xy_all
    - self.x
    - self.y_raw
    - self.y_bg
    - self.y_fit
    - self.xy_eles
    - self.y_eles  # y-axis extraction from self.xy_eles.
    - self.element_peaknames


    MultiIndex columns of self.xy_all look like this:
    ---------------------------------------------------------
    | base                       | bg  | peak               | ...
    ---------------------------------------------------------
    |  x   | y_raw| y_bg | y_fit | bg1 | ele1 | ele2 | ele3 | ...
    ---------------------------------------------------------
    | ...  | ...  | ...  | ...   |     | ...  | ...  | ...  | ...
    ---------------------------------------------------------
    """

    ID_XY_ALL   = "xy_all"
    ID_XY_RAW   = "xy_raw"
    ID_Y_RAW    = "y_raw"
    ID_Y_BG     = "y_bg"
    ID_Y_FIT    = "y_fit"

    ID_FIRST_BASE      = "base"
    ID_FIRST_BG        = "bg"
    ID_FIRST_PEAK      = "peak"

    ID_SECOND_X     = "x"
    ID_SECOND_RAW   = "y_raw"
    ID_SECOND_BG    = "y_bg"
    ID_SECOND_FIT   = "y_fit"

    #BASIC_COLS = [
    #    ID_X,
    #    ID_Y_RAW,
    #    ID_Y_BG,
    #    ID_Y_FIT,
    #]

    # Define a minimum set of MultiIndex columns of xySeries, 
    # where the first level is "base".
    INIT_MULTI_COLMN = [
        (ID_FIRST_BASE,     ID_SECOND_X    ),
        (ID_FIRST_BASE,     ID_SECOND_RAW  ),
        (ID_FIRST_BASE,     ID_SECOND_BG   ), 
        (ID_FIRST_BASE,     ID_SECOND_FIT  ), 
    ]

    ID_FIRST = "first"
    ID_SECOND = "second"
    COLUMN_LEVELS = [ID_FIRST, ID_SECOND]

    INIT_COLS = pd.MultiIndex.from_tuples(INIT_MULTI_COLMN, names=COLUMN_LEVELS)


    def __init__(
        self, 
        x           : pd.Series | np.ndarray | None = None,
        raw         : pd.Series | np.ndarray | None = None,
        loaded_data : pd.DataFrame                  = None,
    ):

        if (x is None) and (raw is None) and (loaded_data is None):
            raise

        if loaded_data is not None:
            df_init     = loaded_data

        if (x is not None) and (raw is not None):
            df_init     = pd.DataFrame(
                data    = None,
                columns = self.INIT_COLS,
            )

            df_init[self.ID_FIRST_BASE, self.ID_SECOND_X]     = x
            df_init[self.ID_FIRST_BASE, self.ID_SECOND_RAW]   = raw

        self.__xy_all   = df_init


    #def _rename_column_y_to_y_raw(self, xy: pd.DataFrame):
    #    if "y" in xy.columns:
    #        xy_rtn = xy.rename(columns={"y": self.ID_Y_RAW})
    #    else:
    #        xy_rtn = xy
    #    return xy_rtn

    #def _drop_unnamed_columns(self, df: pd.DataFrame):
    #    cols_to_drop = df.columns[df.columns.str.contains('Unnamed:', case=False)]
    #    df_cleaned = df.drop(columns=cols_to_drop)
    #    return df_cleaned



    def _ndlist_to_serieslist(self, nds: list) -> list:
        rtn = []
        for nd in nds:
            rtn.append(pd.Series(nd))
        return rtn

    def to_df(self) -> pd.DataFrame:
        return self.xy_all
    
    def has_bg(self) -> bool:
        return self.has_bg_elements


    @property
    def xy_all(self) -> pd.DataFrame:
        return self.__xy_all

    @property
    def all(self) -> pd.DataFrame:
        """Short for xy_all"""
        return self.xy_all

    def update_xy_all(self, df: pd.DataFrame):
        self.__xy_all = df
        return

    @property
    def bases(self) -> pd.DataFrame:
        """
        Return pandas.DataFrame where the main column is "base".
        """
        return self.all[self.ID_FIRST_BASE]

    @property
    def bgs(self) -> pd.DataFrame:
        """
        Return pandas.DataFrame where the main column is "bg".
        """
        return self.all[self.ID_FIRST_BG]

    @property
    def peaks(self) -> pd.DataFrame:
        """
        Return pandas.DataFrame where the main column is "peak".
        """
        return self.all[self.ID_FIRST_PEAK]

    #@property
    #def extra(self):
    #    return self.__extra

    @property
    def x(self) -> pd.Series:
        return self.all[self.ID_FIRST_BASE, self.ID_SECOND_X]

    def update_x(self, ser: pd.Series):
        self.all[self.ID_FIRST_BASE, self.ID_SECOND_X] = ser
        return

    def xshift(self, shift: float):
        self.all[self.ID_FIRST_BASE, self.ID_SECOND_X] = self.all[
            self.ID_FIRST_BASE, self.ID_SECOND_X].add(shift)
        return

    @property
    def xy_raw(self) -> pd.DataFrame:
        locator = [
            (self.ID_FIRST_BASE, self.ID_SECOND_X), 
            (self.ID_FIRST_BASE, self.ID_SECOND_RAW)
        ]
        return self.all.loc[:, locator]

    @property
    def y_raw(self) -> pd.Series:
        return self.all[self.ID_FIRST_BASE, self.ID_SECOND_RAW]

    @property
    def raw(self) -> pd.Series:
        """Short for self.raw"""
        return self.y_raw

    #@property
    #def y(self):
    #    """
    #    Shortcut for `y_raw`.
    #    """
    #    return self.xy_all[self.ID_Y_RAW]

    def update_raw(self, ser: pd.Series):
        self.xy_all[self.ID_FIRST_BASE, self.ID_SECOND_RAW] = ser
        return

    @property
    def y_bg(self) -> pd.Series:
        """Total of backgrounds."""
        return self.all[self.ID_FIRST_BASE, self.ID_SECOND_BG]

    @property
    def bg(self):
        """Short for self.bg"""
        return self.y_bg

    def update_bg(
        self, 
        ser: pd.Series | None = None,
    ):
        if ser is not None:  # for backward compatibility
            self.all[self.ID_FIRST_BASE, self.ID_SECOND_BG] = ser

        elif self.has_bg_elements():
            s = self.all[self.ID_FIRST_BG].sum(axis=1, skipna=False)  # Sum of all columns in BG level
            self.all[self.ID_FIRST_BASE, self.ID_SECOND_BG] = s
        
        else:
            raise

        return

    def update_y_bg(
        self, 
        ser: pd.Series | None = None,
    ):
        return self.update_bg(ser)  # Wrapper for backward compatibility
    
    def has_bg_elements(self) -> bool:
        flag_list = self.all.columns.isin({self.ID_FIRST_BG}, level=0)
        return flag_list.any()

    def update_bg_element(
        self, 
        ser: pd.Series | np.ndarray, 
        column_name
    ):
        # update or create a new column of bg.
        self.all[self.ID_FIRST_BG, column_name] = ser
        self.update_bg()
        return

    @property
    def y_raw_without_bg(self) -> pd.Series:
        return self.raw - self.bg

    @property
    def y_fit(self) -> pd.Series:
        return self.all[self.ID_FIRST_BASE, self.ID_SECOND_FIT]

    @property
    def fit(self) -> pd.Series:
        return self.y_fit

    def update_y_fit(self, ser: pd.Series | np.ndarray):
        self.all[self.ID_FIRST_BASE, self.ID_SECOND_FIT] = ser
        return

    #@property
    #def xy_eles(self):
    #    col = [self.ID_X] + self.columns_elements
    #    return self.xy_all[col]

    @property
    def y_eles(self):
        """Short for self.peak"""
        return self.peaks

    #def update_y_eles(self, eles: pd.DataFrame):
    #    new_xy_all_list = [self.xy_all, eles]
    #    self.update_xy_all(pd.concat(new_xy_all_list, axis="columns"))
    #    return

    def update_peak_element(
        self, 
        ser: pd.Series | np.ndarray, 
        column_name
    ):
        # update or create a new column of peak.
        self.all[self.ID_FIRST_PEAK, column_name] = ser
        # No need to update `fit` column.
        return

    @property
    def columns(self):
        return self.all.columns

    #@property
    #def columns_elements(self):
    #    return self.columns_peaks

    @property
    def columns_peaks(self):
        col = self.peaks.columns
        return col

    @property
    def columns_bgs(self):
        col = self.bgs.columns
        return col
    
    @property
    def residual(self):
        return self.raw - self.fit
    
    def has_bg(self):
        #print(f"Columns:\n{self.all.columns.get_level_values(0).isin(["bg"])}\n")
        l = self.all.columns.get_level_values(0).isin([self.ID_FIRST_BG])
        return l.any()