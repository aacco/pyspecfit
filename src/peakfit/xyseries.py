import peakfit
from . import common as cmn
from . import model as mdl
from . import background as bg
import pandas as pd
import matplotlib.pyplot as plt
import scipy
import scipy.optimize
import numpy as np

class xySeries:
    """
    Wrapper class of pandas.DataFrame for fitting.
    - self.xy_all
    - self.x
    - self.y_raw
    - self.y_bg
    - self.y_fit
    - self.xy_eles
    - self.y_eles  # y-axis extraction from self.xy_eles.
    - self.element_peaknames
    """

    ID_X        = "x"
    ID_XY_ALL   = "xy_all"
    ID_XY_RAW   = "xy_raw"
    ID_Y_RAW    = "y_raw"
    ID_Y_BG     = "y_bg"
    ID_Y_FIT    = "y_fit"
    FUNDAMENTAL_COLS = [
        ID_X,
        ID_Y_RAW,
        ID_Y_BG,
        ID_Y_FIT,
    ]

    def __init__(self, xy: pd.DataFrame):
        xy_renamed = self._rename_column_y_to_y_raw(xy)
        xy_cleaned = self._drop_unnamed_columns(xy_renamed)

        self.__xy_all     = xy_cleaned

    def _rename_column_y_to_y_raw(self, xy: pd.DataFrame):
        if "y" in xy.columns:
            xy_rtn = xy.rename(columns={"y": self.ID_Y_RAW})
        else:
            xy_rtn = xy
        return xy_rtn

    def _drop_unnamed_columns(self, df: pd.DataFrame):
        cols_to_drop = df.columns[df.columns.str.contains('Unnamed:', case=False)]
        df_cleaned = df.drop(columns=cols_to_drop)
        return df_cleaned



    def _ndlist_to_serieslist(self, nds: list) -> list:
        rtn = []
        for nd in nds:
            rtn.append(pd.Series(nd))
        return rtn

    @property
    def xy_all(self):
        return self.__xy_all

    def update_xy_all(self, df: pd.DataFrame):
        self.__xy_all = df
        return

    @property
    def all(self):
        """Short for xy_all"""
        return self.xy_all

    @property
    def xy_raw(self):
        return self.xy_all[[self.ID_X, self.ID_Y_RAW]]

    @property
    def raw(self):
        """Short for xy_raw"""
        return self.xy_raw

    @property
    def x(self):
        return self.xy_all[self.ID_X]

    def update_x(self, ser: pd.Series):
        self.xy_all[self.ID_X] = ser
        return

    @property
    def y_raw(self):
        return self.xy_all[self.ID_Y_RAW]

    def update_y_raw(self, ser: pd.Series):
        self.xy_all[self.ID_Y_RAW] = ser
        return

    @property
    def y_bg(self):
        return self.xy_all[self.ID_Y_BG]

    def update_y_bg(self, ser: pd.Series):
        self.xy_all[self.ID_Y_BG] = ser
        return

    @property
    def y_raw_without_bg(self):
        return self.xy_all[self.ID_Y_RAW] - self.xy_all[self.ID_Y_BG]

    @property
    def y_fit(self):
        return self.xy_all[self.ID_Y_FIT]

    def update_y_fit(self, ser: pd.Series):
        self.xy_all[self.ID_Y_FIT] = ser
        return

    @property
    def xy_eles(self):
        col = [self.ID_X] + self.columns_elements
        return self.xy_all[col]

    @property
    def y_eles(self):
        return self.xy_all[self.columns_elements]

    def update_y_eles(self, eles: pd.DataFrame):
        new_xy_all_list = [self.xy_all, eles]
        self.update_xy_all(pd.concat(new_xy_all_list, axis="columns"))
        return

    @property
    def columns(self):
        return self.xy_all.columns

    @property
    def columns_elements(self):
        ele_list = [c for c in self.columns if not c in self.FUNDAMENTAL_COLS]
        return ele_list