import os
import json
import numpy as np
import pandas as pd
import scipy

from . import common as cmn


C1S_POS = 284.6
COL_NAMES = ["Binding energy [eV]", "Intensity"]  # colunm 1 to 2
CSV_EXT = ".csv"
BACKGROUND_LOOP_LIMIT = 100

XPS     = "XPS"
XPS_PARAMS = {
    "xlabel": r"$Binding energy \left[eV\right]$",
    "ylabel": "Intensity [cps]",
}

def csv_path(base_dir_path: str, csv_name: str):
    return base_dir_path + csv_name + CSV_EXT

def processed_dir_target(base_dir_path: str, csv_name: str):
    return base_dir_path + csv_name + "_processed"

def read_csv(csv_path: str, dataframe = False):
    """
    Wrapper of pandas.read_csv for XPS csv-file style.
    """
    _df1 = pd.read_csv(csv_path, names=COL_NAMES)
    _df = _df1.fillna('')
    bi = _df[COL_NAMES[0]].apply(cmn.is_only_floats)  # gain bool index of raw data area.
    df = _df[bi]  # raw data table.
    num_df = df.astype(float)  # Convert str to float.
    xy = num_df.to_numpy()  # Convert pandas.dataframe to numpy.ndarray.
    xy = xy.T  # Transposition of xy
    #print(xy)
    if dataframe:
        xy = pd.DataFrame({"x": xy[0], "y":xy[1]})
    return xy

def divide_spectra(df1):
    # Divide raw CSV data into each spectrum (eg. C1s) by appearance of the word "Area1" before each area of narrow scan data in CSV.
    '''
    Example of df1: 

        Binding energy [eV]  Intensity
    0                  Area1            <- identifier
    1                   Zr3d
    2                      1
    3               194.0000  3168.6794
    4               193.9500  3060.3988
    ...                  ...        ...
    1611            278.2000  3797.9324
    1612            278.1500  3690.3627
    1613            278.1000  3841.2665
    1614            278.0500  3836.0585
    1615            278.0000  3658.9251
    '''
    idxs_Area1 = df1[df1[COL_NAMES[0]] == "Area1"].iloc[:]  # Locating indexes of "Area1" in the raw data.
    iA1 = idxs_Area1.index

    dfs = []  # Array of divided spectrum data (eg. C1s, O1s, etc.)
    for i in range(0, len(iA1)):
        if i == len(iA1) - 1:  # For last "Area1" spectrum.
            df = df1[iA1[i]:]
            df.iat[2, 0] = ''
            dfs.append(df)
        else:                   # For first ~ 2nd last spectrum.
            df = df1[iA1[i]:iA1[i + 1]]
            df.iat[2, 0] = ''
            dfs.append(df)

    #print(dfs[0].iloc[1, 0])
    #print(dfs[1])
    return dfs

def to_csvs(dfs, dir_target: str, csv_name: str):
    if (not os.path.isdir(dir_target)):  # Make save directory if not exsit.
        os.mkdir(dir_target)

    for df in dfs:  # Save each spectra data.
        material_name = df.iloc[1, 0]
        csv_target = csv_name + "_" + material_name + CSV_EXT
        df.to_csv(dir_target + "/" + csv_target, index=False)

    return

def read_narrowscan(path: str):
    _df1 = pd.read_csv(csv_path, names=COL_NAMES)
    _df = _df1.fillna('')
    
    #TODO
    return

def add_y(xy1, xy2):
    xy_r = np.array([xy1[0], xy1[1] + xy2[1]])
    return xy_r

def subtract_y(xy1, xy2):
    xy_r = np.array([xy1[0], xy1[1] - xy2[1]])
    return xy_r

def linear(x, a, b):
    return a * x + b

def voigt(x, params):
    """
    # param:
    x_pos   : Center of Lorentzian line.
    gamma     : Gamma of Lorentzian (equal to FWHM of Lorentzian).
    sigma     : Sigma of Gaussian (equal to standard deviation of Gaussian).
    norm      : Normalization (default = 1).
    """
    #print(params)
    x_pos, gamma, sigma, norm = params
    z = (x - x_pos + 1j * gamma) / (sigma * np.sqrt(2.0))
    w = scipy.special.wofz(z)
    v = norm * (w.real) / (sigma * np.sqrt(2.0 * np.pi))
    return v

def singlet(x, params):
    """
    Wrapper of single voight function.
    """
    return voigt(x, params)

def doublet(x, d_ratio, d_shift, params):
    """
    # Arguments
    x         : List of x [eV] within fit range.
    d_ratio   : Doublet ratio (ratio of intensity between main peak and sub peak).
    d_shift   : Doublet shift (position shift between main peak and sub peak).
    params: list
        - x_pos     : Center of Lorentzian line.
        - gamma     : Gamma of Lorentzian (equal to FWHM of Lorentzian).
        - sigma     : Sigma of Gaussian (equal to standard deviation of Gaussian).
        - norm      : Normalization (default = 1).
    """
    main_peak = voigt(x, params)
    sub_params = [params[0] + d_shift, params[1], params[2], params[3] * d_ratio]
    sub_peak = voigt(x, sub_params)
    return main_peak + sub_peak

def trim_xy(xy, range: tuple):
    x_start = range[1]  # Upper limit of eV range (lower limit of index). NOtICE: x axis is inversed, and x_start means left-side of XPS graph (inversed [eV]).
    x_end= range[0]     # Lower limit of eV range (upper limit of index).
    #print("DEBUG")
    #print(xy[0])
    #print(x_start)
    index_start = np.where(xy[0] >= x_start)[0][-1]  # x is in descending order, so index_start (upper eV limit) is the end of xy[0] >= x_start
    index_end   = np.where(xy[0] <= x_end)[0][0] + 1
    #print("trim_xy:")
    #print(f"    index_start: {index_start}")
    #print(f"    index_end: {index_end}")
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

def fit_bg_linear(xy, range: tuple):
    '''
    Calculate linear background from neighborhood of peaks.
    Ref.: A. Herrera-Gomez, et al., Surf. Interface Anal., vol. 46, no. 10–11, pp. 897–905, Oct. 2014.
    '''
    _, x_trimmed, y_trimmed, _ = trim_xy(xy, range)
    popt, _ = scipy.optimize.curve_fit(linear, x_trimmed, y_trimmed)

    baseline = np.array([xy[0], linear(xy[0], *popt)])
    return baseline

def fit_bg_shirley(xy, fitting_range: tuple):
    '''
    Fitting range [eV]
    '''
    print("fit_bg_shirley:")
    _, x_list_clipped, y_list_clipped, h = trim_xy(xy, fitting_range)

    B_list = np.full(len(x_list_clipped), y_list_clipped[0])  # Initialize background (Blist).
    #B_list = np.full(len(x_list_clipped), 0)  # Initialize background (Blist).
    #print(B_list)
    J_list = y_list_clipped.copy()  # Initialize
    area_P_plus_Q = 0  # Initialize
    area_P_plus_Q_old = 0  # Initialize
    for i in range(BACKGROUND_LOOP_LIMIT):
        for j in range(J_list.size):
            #print(F_list)
            #print("B_list")
            #print(B_list)
            area_Q          = h * (np.sum(J_list[j:] - B_list[j:])  - 0.5 * (J_list[j] - B_list[j] + J_list[-1] - B_list[-1]))
            area_P_plus_Q   = h * (np.sum(J_list - B_list)          - 0.5 * (J_list[0] - B_list[0] + J_list[-1] - B_list[-1]))
            B_list[j] = (y_list_clipped[0] - y_list_clipped[-1]) * area_Q / area_P_plus_Q + y_list_clipped[-1]
            #F_list = y_list_clipped - B_list

        print(f"    Loop_no.: {i}, P+Q: {round(area_P_plus_Q, 5)} (delta: {round((area_P_plus_Q - area_P_plus_Q_old) / area_P_plus_Q * 100, 5)}%)")
        if (abs(area_P_plus_Q - area_P_plus_Q_old) < abs(area_P_plus_Q) * 0.0001):
            break
        elif i >= BACKGROUND_LOOP_LIMIT - 1:
            print("Background calculation time out.")
            raise

        area_P_plus_Q_old = area_P_plus_Q

    return np.array([x_list_clipped, B_list])

def fit_bg(xy_raw, range_linear, range_shirley):
    _xy_bg_linear = fit_bg_linear(xy_raw, range_linear)             # Fitting linear-slope component of backgrounds.
    xy_bg_linear, _, _, _ = trim_xy(_xy_bg_linear, range_shirley)   # Trim the slope range (full range) to fit shirley range.

    xy_wo_baseline = subtract_y(xy_raw, _xy_bg_linear)                # Subtraction between raw data and linear background.
    xy_bg_shirley = fit_bg_shirley(xy_wo_baseline, range_shirley)     # Fitting Shirley component.

    xy_bg_total = add_y(xy_bg_linear, xy_bg_shirley)
    return  xy_bg_total

def baseline(xy: pd.DataFrame, range: tuple):
    '''
    Calculate linear background from neighborhood of peaks.
    Ref.: A. Herrera-Gomez, et al., Surf. Interface Anal., vol. 46, no. 10–11, pp. 897–905, Oct. 2014.
    '''
    xy_clipped = cmn.xclip(xy, range, reset_index=False)
    popt, _ = scipy.optimize.curve_fit(linear, xy_clipped.x, xy_clipped.y)

    bl = pd.DataFrame({"x":xy.x, "y": linear(xy.x, *popt)})
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

        print(f"    Loop_no.: {i}, P+Q: {round(area_P_plus_Q, 5)} (delta: {round((area_P_plus_Q - area_P_plus_Q_old) / area_P_plus_Q * 100, 5)}%)")

        if (abs(area_P_plus_Q - area_P_plus_Q_old) < abs(area_P_plus_Q) * 0.0001):
            break

        elif i >= BACKGROUND_LOOP_LIMIT - 1:
            print("Background calculation excessed loop limit.")
            raise

        area_P_plus_Q_old = area_P_plus_Q


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

def load_init_peak(path: str):
    """
    Return range_linear, range_peak, parse_result

    parse_result = {
        "chem_shifts": ["C-C", ...(all chemical shift names)...],
        "chem-shift name (e.g. C-C)": {
            "init": [position_init, gamma_init, sigma_init, norm_init],
            "bounds": [
                    [min_x_pos, min_gamma, min_sigma, min_norm],
                    [max_x_pos, max_gamma, max_sigma, max_norm]
            ],
        },
        ...
    }

    Example json file:
    - C1s (<- this is peak_name)
        - Range
            - Fit
            - Linear
        - Peaks
            - C-C
                - Position
                - Gamma
                - Sigma
                - Norm
    """
    with open(path) as f:
        j = json.load(f)

        # Key shortner
        posi = "Position"
        gamm = "Gamma"
        sigm = "Sigma"
        norm = "Norm"
        d_ra = "Doublet_Ratio"
        d_sh = "Doublet_Shift"
        init = "Initial_guess"
        lo   = "Lower_limit"
        up   = "Upper_limit"

        peak_name = list(j.keys())[0]  # E.g. C1s, O1s ...
        peaks_ranges = j[peak_name]["Range"]
        peaks = j[peak_name]["Peaks"]

        # Range loading
        range_peak      = (peaks_ranges["Fit"]["Start"],    peaks_ranges["Fit"]["End"])
        range_linear    = (peaks_ranges["Linear"]["Start"], peaks_ranges["Linear"]["End"])

        parse_result = {
            "chem_shifts":  [],
            "inits":        [],         # initial guesses in a list with shape (n,).
            "bounds":       [[], []],   # bounds in a list with shape (n,2).
        }

        for chem_shift_key in peaks:  # For each chemical-shifted peak (e.g. "C-C" in C1s range.)
            # Initial guess loading
            chem_shift_peak = peaks[chem_shift_key]
            if not chem_shift_peak["Use"]:
                continue

            parse_result["chem_shifts"].append(chem_shift_key)
            pr = parse_result[chem_shift_key] = {}  # Append new chemical shift key

            param_keys = [posi, gamm, sigm, norm]  # Necessary keys for peak (both singlet and doublet).
            if d_ra in chem_shift_peak:  # Additional keys only for doublets.
                param_keys.append(d_ra)
                param_keys.append(d_sh)

            _params_init = []
            for p in param_keys:
                _params_init.append(chem_shift_peak[p][init])
            #position_init = chem_shift_peak[posi][init]
            #gamma_init    = chem_shift_peak[gamm][init]
            #sigma_init    = chem_shift_peak[sigm][init]
            #norm_init     = chem_shift_peak[norm][init]
            params_init   = np.array(_params_init)
            pr["init"] = params_init  # Append initial guesses
            for i in params_init:
                parse_result["inits"].append(i)  # "inits" is an array of (n,)-shape.

            # Bounds loading
            mins = []
            maxs = []
            for i_p in param_keys:
                if chem_shift_peak[i_p]["Hold"]:
                    # Hold condition around initial guess value.
                    _min = chem_shift_peak[i_p][init] - 1e-10
                    _max = chem_shift_peak[i_p][init] + 1e-10
                else:
                    # loading condition from json file.
                    _min = parse_null(chem_shift_peak[i_p][lo], "min")
                    _max = parse_null(chem_shift_peak[i_p][up], "max")
                mins.append(_min)
                maxs.append(_max)
    
            fit_bounds = [
                mins,  # Minimum of each arguments of Voigt: x_pos, gamma, sigma, norm
                maxs   # Maximum of each arguments of Voigt
            ]
            pr["bounds"] = fit_bounds  # Append boundaries

            for min in mins:
                parse_result["bounds"][0].append(min)
            for max in maxs:
                parse_result["bounds"][1].append(max)

    #r = {
    #    "r_linear": range_linear,
    #    "r_peak": range_peak,
    #    "parse": parse_result,
    #    "chmical_shifts": chem_shift_peak
    #}
    return range_linear, range_peak, parse_result

def chi_squared(params, model_func, x, y, y_errors): # TODO: check
    # Residual function: chi-squared testing
    model = model_func(x, params)
    chi = (y - model) / y_errors
    return chi

def residual(params, model_func, x, y):
    model = model_func(x, params)
    return y - model

def print_fit_result(params_result, chem_shifts, mode="singlet"):
    # TODO: multi-peak
    print(f"Fit result:")
    if mode == "singlet":
        for i, p in enumerate(chem_shifts):
            print(f"    {p}")
            print(f"        Position:  {params_result[i*4]}")
            print(f"        Gamma:     {params_result[i*4+1]}")
            print(f"        Sigma:     {params_result[i*4+2]}")
            print(f"        Norm:      {params_result[i*4+3]}")
    elif mode == "doublet":
        for i, p in enumerate(chem_shifts):
            print(f"    {p}")
            print(f"        Position:  {params_result[i*6]}")
            print(f"        Gamma:     {params_result[i*6+1]}")
            print(f"        Sigma:     {params_result[i*6+2]}")
            print(f"        Norm:      {params_result[i*6+3]}")
            print(f"        D-ratio:   {params_result[i*6+4]}")
            print(f"        D-shift:   {params_result[i*6+5]}")
    else:
        print(params_result)
    return

def fit(xy, range_peak, range_linear, params_init, bounds, fit_args):
    xy_bg = fit_bg(xy, range_linear, range_peak)
    
    fit_output = scipy.optimize.least_squares(
    # Minimizing residual function
    residual,               # Function of residuals
    params_init,            # Initial guessing value of fitting
    bounds = bounds,        # Limit of fitting
    args = fit_args         # Arguments passed to residual functions e.g. fun(x, *args, **kwargs)
    )

    # TODO: rest.
    return fit_output


def chunk_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def shift_x(xy, x_shift: float):
    return np.array([xy[0] + (C1S_POS - x_shift), xy[1]])

def plot_elements(ax, xy_bg, fit_params, chem_shifts, peaktype="singlet", model=voigt):
    if peaktype == "singlet":
        chunk_num = 4
    else:
        chunk_num = 6
    chunk_params = chunk_list(fit_params, chunk_num)
    rtn = pd.DataFrame({"x": xy_bg[0]})
    for i, p in enumerate(chunk_params):
        y_ele = model(xy_bg[0], p)
        xy_ele = [xy_bg[0], xy_bg[1] + y_ele]
        kw = {
            "label": chem_shifts[i]
        }
        cmn.plot(ax, xy_ele, **kw)
        #rtn[chem_shifts[i]] = xy_ele[1]  # w/ bg
        rtn[chem_shifts[i]] = y_ele  # w/o bg
    return rtn

def plot_elements_filled(ax, xy_bg, fit_params, chem_shifts, peaktype="singlet", model=voigt):
    if peaktype == "singlet":
        chunk_num = 4
    else:
        chunk_num = 6
    chunk_params = chunk_list(fit_params, chunk_num)
    xy_list = []
    for i, p in enumerate(chunk_params):
        xy_ele = [xy_bg[0], xy_bg[1] + model(xy_bg[0], p)]
        kw = {
            "label": chem_shifts[i],
            "alpha": 0.25
        }
        xy_list.append([chem_shifts[i], xy_ele])
        #cmn.plot(ax, xy_ele, **kw)
        #xy_bg_trimed, _, _, _ = trim_xy(xy_bg, (xy_ele[0][-1], xy_ele[0][0]))
        #print("xy_ele: " + str(len(xy_ele[0])))
        #print("xy_bg_trimed: " + str(len(xy_bg[0])))
        #print(xy_bg[0][0])
        #print(xy_ele[0][0])
        ax.fill_between(xy_ele[0], xy_ele[1], xy_bg[1], **kw)
    return xy_list

def multifit():
    return

def fit_C1s(csv_path: str):
    path_json = f"./python/local/xps_fit_param/C1s.json"

    # Loading
    xy = read_csv(csv_path)
    range_linear, range_C1s, parse_C1s = load_init_peak(path_json) 

    # Fitting
    xy_bg = fit_bg(xy, range_linear, range_C1s)
    xy_trimed, _, _, _ = trim_xy(xy, range_C1s)
    xy_subbg = subtract_y(xy_trimed, xy_bg)

    fit_args = (
        voigt,              # Fit model function
        xy_subbg[0],            # x-axis list of fitting range w/o background
        xy_subbg[1],            # y-axis list of fitting range w/o background
        #np.sqrt(xy_subbg[1])   # y-axis errors list of fitting range
    )

    #print(parse_C1s)
    #print(parse_C1s["C-C"]["init"])
    #print(parse_C1s["C-C"]["bounds"])
    fit_output = scipy.optimize.least_squares(
        # Minimizing residual function
        residual,               # Function of residuals
        parse_C1s["C-C"]["init"],            # Initial guessing value of fitting
        bounds = parse_C1s["C-C"]["bounds"],    # Limit of fitting
        args = fit_args         # Arguments passed to residual functions e.g. fun(x, *args, **kwargs)
    )


    params_result = fit_output.x
    #print_fit_result(params_result)

    xy_fit = np.array([xy_bg[0], xy_bg[1] + voigt(xy_bg[0], params_result)])  # Build up overall fit-curve shape
    result = {
        "raw": xy,
        "fit": xy_fit,
        "bg": xy_bg,
        "params": params_result
    }
    return result

