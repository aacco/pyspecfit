import os
import json
import numpy as np
import pandas as pd
import scipy

from . import common as cmn
from . import model as mdl


C1S_POS = 284.6
COL_NAMES = ["Binding energy [eV]", "Intensity"]  # colunm 1 to 2
CSV_EXT = ".csv"
BACKGROUND_LOOP_LIMIT = 100

XPS     = "XPS"
XPS_PARAMS = {
    "xlabel": r"$Binding energy \left[eV\right]$",
    "ylabel": "Intensity [cps]",
}


def _add_y(xy1, xy2):
    xy_r = np.array([xy1[0], xy1[1] + xy2[1]])
    return xy_r

def _subtract_y(xy1, xy2):
    xy_r = np.array([xy1[0], xy1[1] - xy2[1]])
    return xy_r

def _trim_xy(xy, range: tuple):
    x_start = range[1]  # Upper limit of eV range (lower limit of index). NOtICE: x axis is inversed, and x_start means left-side of XPS graph (inversed [eV]).
    x_end= range[0]     # Lower limit of eV range (upper limit of index).

    index_start = np.where(xy[0] >= x_start)[0][-1]  # x is in descending order, so index_start (upper eV limit) is the end of xy[0] >= x_start
    index_end   = np.where(xy[0] <= x_end)[0][0] + 1

    x_list_trimmed = np.array(xy[0][index_start:index_end])  # In x_list_clipped and y_list_clipped, index_start -> 0, and index_end -> -1
    y_list_trimmed = np.array(xy[1][index_start:index_end])
    if x_list_trimmed.size <= 0:  # error handling
        print("range error")
        raise
    else:
        #print(f"    x_list_clipped.size: {x_list_trimmed.size}")
        pass
    
    xy_trimmed = np.array([x_list_trimmed, y_list_trimmed])

    h = x_list_trimmed[0] - x_list_trimmed[1]  # h is delta_x in data.
    h = round(h, 2)  # for cases such as h = 0.05000000000002

    return xy_trimmed, x_list_trimmed, y_list_trimmed, h

def baseline(xy: pd.DataFrame, range: tuple):
    '''
    Calculate linear background from neighborhood of peaks.
    Ref.: A. Herrera-Gomez, et al., Surf. Interface Anal., vol. 46, no. 10–11, pp. 897–905, Oct. 2014.
    '''
    xy_clipped = cmn.xclip(xy, range, reset_index=False)
    popt, _ = scipy.optimize.curve_fit(mdl.linear, xy_clipped.x, xy_clipped.y)

    bl = pd.DataFrame({"x":xy.x, "y": mdl.linear(xy.x, *popt)})
    return bl

def shirley(
    xy: pd.DataFrame, 
    fitrange: tuple, 
    init_B = None,
):
    print("fit_bg_shirley:")

    xy_clipped = cmn.xclip(xy, fitrange, reset_index=False)
    x_list_clipped = xy_clipped.x.to_numpy()
    y_list_clipped = xy_clipped.y.to_numpy()

    # Initialization
    dx                  = x_list_clipped[1] - x_list_clipped[0]

    if init_B is None:
        B_list          = np.full(len(x_list_clipped), y_list_clipped[0])   # Initialize background (Blist).
    else:
        B_list          = init_B

    J_list              = y_list_clipped.copy()                             # Initialize
    area_P_plus_Q       = 0                                                 # Initialize
    area_P_plus_Q_old   = 0                                                 # Initialize


    for i in range(BACKGROUND_LOOP_LIMIT):
        for j in range(J_list.size):
            area_Q          = dx * (np.sum(J_list[j:] - B_list[j:])  - 0.5 * (J_list[j] - B_list[j] + J_list[-1] - B_list[-1]))
            area_P_plus_Q   = dx * (np.sum(J_list - B_list)          - 0.5 * (J_list[0] - B_list[0] + J_list[-1] - B_list[-1]))
            B_list[j]       = (y_list_clipped[0] - y_list_clipped[-1]) * area_Q / area_P_plus_Q + y_list_clipped[-1]

        print(f"    Loop_no.: {i}, P+Q: {round(area_P_plus_Q * -1, 5)} (delta: {round((area_P_plus_Q - area_P_plus_Q_old) / area_P_plus_Q * 100, 5)}%)")

        if (abs(area_P_plus_Q - area_P_plus_Q_old) < abs(area_P_plus_Q) * 0.0001):
            break

        elif i >= BACKGROUND_LOOP_LIMIT - 1:
            print("Background calculation excessed loop limit.")
            raise

        area_P_plus_Q_old = area_P_plus_Q

    # Returning dataframe consisted of x-axis and Shirley background (y-axis)
    df_rtn = pd.DataFrame(
        {"x": x_list_clipped, "y": B_list},
        index=xy_clipped.index
    )

    return df_rtn

def linear_and_shirley(
    xy              : pd.DataFrame,
    range_linear    : tuple,
    range_shirley   : tuple,
):
    """
    Background fitting algorithm passed to Spectrum.fit_background method.
    """
    xy_raw = xy
    xy_baseline_full = baseline(xy_raw, range_linear)             # Fitting linear-slope component of backgrounds.
    xy_baseline_clipped = cmn.xclip(xy_baseline_full, range_shirley, reset_index=False)   # Trim the slope range (full range) to fit shirley range.

    xy_wo_baseline = pd.DataFrame({"x": xy_raw.x, "y": xy_raw.y - xy_baseline_full.y})                # Subtraction between raw data and linear background.
    xy_bg_shirley = shirley(xy_wo_baseline, range_shirley)     # Fitting Shirley component.

    # CAUTION: avoid misaligned indices.
    y_bg_total = xy_baseline_clipped.y + xy_bg_shirley.y
    df_rtn = pd.DataFrame(
        {
            "x": xy.x,
            "y": xy.y,
            "bg": y_bg_total,
        }
    )
    return  df_rtn

def parse_null(val, mode: str):
        if val == None:
            if mode == "max":
                return np.inf
            elif mode == "min":
                return 0
        else:
            return val

