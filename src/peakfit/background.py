import numpy as np
import pandas as pd
import pybeads

from . import common as cmn

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def __x_index__():
    return

def extend_slope(xy: pd.DataFrame, k=1, d=5,  ratio=False) -> pd.DataFrame:
    """
    ## extend_slope
    - xy:       Raw data
    - k:        Sharpness of sigmoid function.
    - d:        Length of extended slope (in the x dimension).
    - ratio:    The ratio of the one-side extension length to the raw-data full length (default: False).
    """
    # The combination (d=5, k=1) shows tipically a gradual slope.

    x = xy.x
    y = xy.y
    dx = x.iloc[1] - x.iloc[0]
    x_raw_first = x.iloc[0]
    x_raw_last  = x.iloc[-1]
    y_l_norm = y.iloc[0]                    # A norm of right-side sigmoid slope.
    y_r_norm = y.iloc[-1]                   # A norm of left-side sigmoid slope.

    if ratio != False:
        raw_full_length = x.iloc[-1] - x.iloc[0]
        d = ratio / 2 * raw_full_length

    # Building up extention length in x dimension of each side.
    extention_index_size = int(d/dx)        # This is *roughly* equal to an index size of the one-side extention.
    real_d_half = extention_index_size * dx      
    x_d = np.arange(-1*real_d_half, real_d_half, dx)  # Total length of one-side extention in x-dimension.

    x_l = x_d + (x_raw_first - real_d_half)      # Shifting the center of left  extension to (x_raw_first - x_d).
    x_r = x_d + (x_raw_last  + real_d_half)      # Shifting the center of right extension to (x_raw_last  + x_d).
    y_l = y_l_norm * sigmoid( 1 * k * x_d)
    y_r = y_r_norm * sigmoid(-1 * k * x_d)

    x_ext = np.hstack([x_l, x, x_r])
    y_ext = np.hstack([y_l, y, y_r])
    
    rtn = pd.DataFrame({"x": x_ext, "y": y_ext})
    return rtn

def extend(xy: pd.DataFrame, xscale=0.05, rscale=4) -> pd.DataFrame:
    """
    Not recommended.
    """
    x = xy.x
    y = xy.y
    dx = x.iloc[1] - x.iloc[0]
    scl_ext = int(len(xy.x) * xscale)  # Data will be extended to the extend of xscale. scl_ext is an index order.
    _x_lr = np.arange(-1*rscale*scl_ext*dx, rscale*scl_ext*dx, dx)        # One side area of sigmoid zone. rscale: the sharpness of sigmoid bending; scl_ext: the long of extend.
    y_l = y.iloc[0]*sigmoid(1/scl_ext*_x_lr)
    y_r = y.iloc[-1]*sigmoid(-1/scl_ext*_x_lr)
    y_ext = np.hstack([y_l, y, y_r])
    #x_l = np.arange(x.iloc[0]-2*rscale*scl_ext*dx, x.iloc[0], dx)            
    #x_r = np.arange(x.iloc[-1]+dx, x.iloc[-1]+2*rscale*scl_ext*dx, dx)    
    x_l = np.array([x.iloc[0]-dx*(len(_x_lr)-i) for i in range(len(_x_lr))])  # a x array of left-extended
    x_r = np.array([x.iloc[-1]+dx*(i+1) for i in range(len(_x_lr))])          # a x array of right-extended
    x_ext = np.hstack([x_l, x, x_r])
    #print(len(x_l))
    #print(len(y_l))
    #print(len(x_r))
    #print(len(y_r))
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
    """
    signal_est, bg_est, cost = pybeads.beads(xy.y, d, fc, r, Nit, lam0*amp, lam1*amp, lam2*amp, pen, conv=None)

    y_wo_bg = xy.y - bg_est

    data = pd.DataFrame({"x": xy.x, "y": y_wo_bg, "bg": bg_est, "sig_est": signal_est})
    cost_data = pd.DataFrame({"nit": range(Nit), "cost": cost})
    rtn = pd.concat([data, cost_data], axis="columns")
    return rtn