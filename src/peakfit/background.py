import numpy as np
import pandas as pd
import pybeads

from . import common as cmn

BEADS = "beads"
SHIRLEY = "shirley"

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def __x_index__():
    return

def extend_slope(
    xy:         pd.DataFrame,
    steepness:  float = 0.01,
    lscale:     float = 0.3,
) -> pd.DataFrame:
    """
    ## extend_slope()
    - xy:           Raw data as pandas.DataFrame.
    - steepness:    Steepness of sigmoid function.
    - lscale:       The ratio of the one-side extension length 
                    to the raw-data full length (default: False).
    """
    # The combination (steepness=0.01, lscale=0.3) shows tipically a gradual slope.

    x           = xy.x
    y           = xy.y
    dx          = x.iloc[1] - x.iloc[0]
    x_raw_first = x.iloc[0]
    x_raw_last  = x.iloc[-1]

    #
    # A norm of 
    # right-side (y_l_norm) and 
    # left-side  (y_r_norm) sigmoid slope.
    #
    y_l_norm    = y.iloc[0]   
    y_r_norm    = y.iloc[-1]  

    rawdata_full_length = x.iloc[-1] - x.iloc[0]
    oneside_length_half = (lscale * rawdata_full_length) / 2

    #
    # Building up extention length in x dimension of each side.
    # The "extention_index_size" is *roughly* equal to 
    # an index size of the one-side extention.
    #
    extention_half_index_size = int(oneside_length_half / dx)
    real_oneside_length_half = extention_half_index_size * dx
    # The "x_d" is total length of one-side extention in x-dimension.
    x_ext = np.arange(-1 * real_oneside_length_half, real_oneside_length_half, dx)

    #
    # Shifting the center of 
    # left  extension to (x_raw_first - x_d) and
    # right extension to (x_raw_last  + x_d).
    # 
    x_l = x_ext + (x_raw_first - real_oneside_length_half)
    x_r = x_ext + (x_raw_last  + real_oneside_length_half)

    y_l = y_l_norm * sigmoid( 1 * steepness * x_ext)
    y_r = y_r_norm * sigmoid(-1 * steepness * x_ext)

    #
    # Concating raw data and extentions in both x- and y-axis.
    #
    x_extended = np.hstack([x_l, x, x_r])
    y_extended = np.hstack([y_l, y, y_r])
    
    rtn = pd.DataFrame({"x": x_extended, "y": y_extended})

    return rtn

def extend(xy: pd.DataFrame, xscale=0.05, rscale=4) -> pd.DataFrame:
    """
    Not recommended. Use extend_slope()
    """
    x = xy.x
    y = xy.y
    dx = x.iloc[1] - x.iloc[0]
    scl_ext = int(len(xy.x) * xscale)  # Data will be extended to the extend of xscale. The "scl_ext" is an index order.

    # One side area of sigmoid zone.
    #   "rscale": the sharpness of sigmoid bending.
    #   "scl_ext": the long of extend.
    _x_lr = np.arange(
        -1 * rscale * scl_ext * dx,
         1 * rscale * scl_ext * dx,
        dx
    )

    y_l   = y.iloc[0]  * sigmoid( 1 / scl_ext * _x_lr)
    y_r   = y.iloc[-1] * sigmoid(-1 / scl_ext * _x_lr)
    y_ext = np.hstack([y_l, y, y_r])

    x_l   = np.array([x.iloc[0]  - dx * (len(_x_lr) - i)  for i in range(len(_x_lr))])   # a x array of left-extended
    x_r   = np.array([x.iloc[-1] + dx * (i + 1)           for i in range(len(_x_lr))])   # a x array of right-extended
    x_ext = np.hstack([x_l, x, x_r])

    xy_ext = np.array([x_ext, y_ext]).T

    return pd.DataFrame(xy_ext, columns=["x", "y"])


def beads(
    xy: pd.DataFrame, 
    fc    = 0.01,
    d     = 1,
    r     = 6,
    amp   = 0.8,
    lam0  = 0.5,
    lam1  = 5,
    lam2  = 4,
    Nit   = 15,
    pen   = "L1_v2"
) -> pd.DataFrame:
    """
    ## pybeads_helper

    -----
    fc = 0.01 # ハイパスフィルター作成に使うcutoff周波数
    d = 1 # ハイパスフィルター作成時のパラメータ。1でよい。詳細は論文参照。
    r = 6 # 非対称ペナルティの非対称具合
    # 測定データとその微分にかかる正規化パラメータ
    amp = 0.8
    lam0 = 0.5 * amp
    lam1 = 5 * amp
    lam2 = 4 * amp
    # MMアルゴリズムのループ回数
    Nit = 15
    # ペナルティー関数
    pen = 'L1_v2'
    ------
    """
    signal_est, bg_est, cost = pybeads.beads(xy.y, d, fc, r, Nit, lam0*amp, lam1*amp, lam2*amp, pen, conv=None)

    y_wo_bg = xy.y - bg_est

    data = pd.DataFrame({"x": xy.x, "y": y_wo_bg, "bg": bg_est, "sig_est": signal_est})
    cost_data = pd.DataFrame({"nit": range(Nit), "cost": cost})
    result = pd.concat([data, cost_data], axis="columns")

    return result