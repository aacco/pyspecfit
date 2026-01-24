import numpy as np
import pandas as pd

class bgSeries:
    """
    Class for handling a background estimation result.
    An instance of "bgSeries" can have five properties: 
    bg, index, new_x, new_y and other.
    The instance must have "bg" data, 
    while "index", new_x", "new_y" and "other" are optional.
    The "other" property can be used for iterational background estimations
    which requires some values.
    """
    def __init__(
        self,
        bg      : pd.Series | np.ndarray,
        index   : pd.Series | np.ndarray | None = None,
        other   : dict                   | None = None,
    ):
        self.__index        = index
        self.__has_index    = index is not None

        if self.__has_index:
            self.__bg       = pd.Series(data=bg, index=index)
        else:
            self.__bg       = bg

        self.__other        = other
        self.__has_other    = other is not None


    @property
    def bg(self):
        return self.__bg

    @property
    def index(self):
        return self.__index

    @property
    def has_index(self):
        return self.__has_index

    @property
    def other(self):
        return self.__other

    @property
    def has_other(self):
        return self.__has_other
