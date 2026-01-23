import re
import numpy as np
import pandas as pd
import scipy
from matplotlib.ticker import ScalarFormatter
import scipy.optimize

from . import model as mdl

FIND_PEAKS_PROMINENCE_MIN   = 100
SINGLET_PARAM_NUM = 4
DOUBLET_PARAM_NUM = 6

def find_key(ar, x_start, x_end):
    s, e = 0, 0
    for i in range(ar.size):
        if ar[i] <= x_start:
            s = i
            break
    for i in range(ar.size):
        if ar[i] <= x_end:
            e = i
            break
    return [s, e]

def is_only_floats(s):
    return bool(re.fullmatch(r'[+-]?\d*\.\d+', s))  # determine whether input str data means float.

def xlim(xy, xlim_range: tuple):  # should be a class?
    #i_Si_min = np.where(xy[0] >= SILICON_PEAK_RANGE[0])[0][0]
    i_x_min = np.where(xy[0] == xlim_range[0])[0][0]
    i_x_max = np.where(xy[0] == xlim_range[1])[0][0]
    _xy = np.array([xy[0][i_x_min:i_x_max + 1], xy[1][i_x_min:i_x_max + 1]])
    return _xy

def is_descending(xy: pd.DataFrame | None = None, x: any = None):
    if xy is not None:
        return (xy.x[1] - xy.x[0]) < 0
    elif x is not None:
        return (x[1] - x[0]) < 0
    else:
        raise

def x_to_index(x, x_ser: pd.Series | np.ndarray):
    diff = (x_ser - x).abs()
    return diff.idxmin()

def xclip(xy: any, range: tuple, reset_index=True) -> pd.DataFrame:
    """
    Roughly clipping xy data by x-axis range.
    - xy    : pd.Dataframe like including "x" and "y" columns.
    - range : Tuple object as (begin, end).
    """
    #x = xy.x.to_numpy()
    x = xy.x

    if is_descending(xy):
        #i_x_min = np.where(x <= range[1])[0][0]
        #i_x_max = np.where(x <= range[0])[0][0]
        i_x_min = x_to_index(range[1], x)
        i_x_max = x_to_index(range[0], x)
    else:
        #i_x_min = np.where(x >= range[0])[0][0]
        #i_x_max = np.where(x >= range[1])[0][0]
        i_x_min = x_to_index(range[0], x)
        i_x_max = x_to_index(range[1], x)

    
    xy_rtn = xy.loc[ i_x_min : i_x_max ]

    if reset_index:
        xy_rtn = xy_rtn.reset_index(drop=True)

    return xy_rtn

def normalize(xy):
    y = xy[1]
    return [xy[0], y / np.max(y)]

def find_peaks(xy):
    peaks_index, _ = scipy.signal.find_peaks(xy[1], prominence=(FIND_PEAKS_PROMINENCE_MIN, None))
    found = [xy[0][peaks_index], xy[1][peaks_index]]
    print("Peaks are fonund in: ")
    print(xy[0][peaks_index])
    return np.array(found)

def expotent_note_y(ax):
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0,0))
    return

def build_dic_from_fitparams(df_fp: pd.DataFrame):
    """
    Wrapper of extract_fitparams()
    """
    return extract_fitparams(df_fp)

def extract_fitparams(df_fp: pd.DataFrame) -> dict:
    """
    Translating DataFrame of fit parameters to a dict object 
    containing "guesses", "boundaries", "peaknum", "paramnum" keys.
    """
    # Selecting the columns which key includes '_guess'.
    guess_columns = [col for col in df_fp.columns if '_guess' in col]
    df_guess = df_fp[guess_columns]

    peaks_num = df_guess.shape[0]   # Number of peaks
    params_num = df_guess.shape[1]  # Column numbers -> chunk_num
    
    # Extracting guess values to "guesses" list.
    guesses = []
    for index, _row in df_guess.iterrows():
        _row = np.array(_row)
        row = _row[~np.isnan(_row)] # Droping nan cell.
        guesses.extend(row)

    # Extracting lower limit values "lower" list.
    lower_columns = [col for col in df_fp.columns if '_lower' in col]
    df_lower = df_fp[lower_columns]
    lower = []
    for index, _row in df_lower.iterrows():
        __row = _row.astype(float)
        _row = np.array(__row)

        row = _row[~np.isnan(_row)] # Droping nan cell.
        # Set the limit to "-np.inf" if lower_limit == False == 0.0.
        # However, the "-np.inf" lower conditions is not used.
        # row[row == 0.0] = -np.inf
        lower.extend(row)

    # Extracting upper limit values "upper" list.
    upper_columns = [col for col in df_fp.columns if '_upper' in col]
    df_upper = df_fp[upper_columns]
    boundaries = []
    upper = []
    for index, _row in df_upper.iterrows():
        _row = _row.astype(float)
        _row = np.array(_row)

        row = _row[~np.isnan(_row)] # Droping nan cell.
        # Set the limit to "np.inf" if upper_limit == False == 0.0.
        row[row == 0.0] = np.inf 
        upper.extend(row)

    # Extracting hold conditions.

    # If "hold_mask" is true, the corresponding parameter is fixed.
    hold_columns = np.array([col for col in df_fp.columns if '_hold' in col])
    _hold_mask = df_fp[hold_columns].values

    # Converting (n, m)-shaped "hold_mask" ndarray to boolean (1, n*m)-shaped ndarray object.
    _hold_mask = _hold_mask.reshape(peaks_num*params_num,)
    # Dropping NA values in boolean array via pd.DataFrame.
    _temp_df_hm = pd.DataFrame(_hold_mask)
    temp_df_hm = _temp_df_hm.dropna()
    temp_hold_mask = temp_df_hm.values.reshape((temp_df_hm.size,))
    hold_mask = temp_hold_mask.astype(bool)

    # Screening lower/upper values by hold_mask.
    # A lower/upper condition array consists of 
    # original lower/upper value    (when "hold_mask" == True), and
    # "guesses" plus-minus 0.000001 (when "hold_mask" == False).
    lower_masked_inverse = np.where(~hold_mask, lower,   0)
    upper_masked_inverse = np.where(~hold_mask, upper,   0)
    guess_masked         = np.where(hold_mask,  guesses, 0)

    # Realize a fixed parameter by setting its range 
    # within the guessing value \pm 0.000001.
    lower_including_hold = lower_masked_inverse + guess_masked - 0.000001
    upper_including_hold = upper_masked_inverse + guess_masked + 0.000001

    boundaries = [lower_including_hold, upper_including_hold]

    return {
        "guesses"   : guesses,
        "boundaries": boundaries,
        "peaknum"   : peaks_num,
        "paramnum"  : params_num,
        "peak_type" : df_fp["peak_type"],
    }

def build_df_elements(x, df_resultparams: pd.DataFrame, chunk_num: int, model=mdl.voigt) -> pd.DataFrame:
    df_eles = pd.DataFrame({"x": x})
    for _, ser in df_resultparams.iterrows():
        arr = ser[['position', 'gamma', 'sigma', 'norm']].values
        y = model(x.values, arr)
        df_eles[ser["peak_name"]] = y
    return df_eles

def build_peak_elements(x, fitresult: scipy.optimize.OptimizeResult, fitparam: pd.DataFrame) -> pd.DataFrame:
    peakname_list = fitparam["peak_name"].to_list()
    peaktype_list = fitparam["peak_type"].to_list()
    chunk_length_list = convert_peak_type_to_chunk_length(peaktype_list)
    # Separating args by each peak type (singlet or doublet).
    params = separate_chunk(fitresult.x, chunk_length_list)

    xy_list = pd.DataFrame({"x": x})
    for i, p in enumerate(params):            # "p" equals [x_pos, gamma, sigma, norm, (d_ratio), (d_shift)].
        L = len(p)
        if   L == SINGLET_PARAM_NUM:
            peak = mdl.singlet
        elif L == DOUBLET_PARAM_NUM:
            peak = mdl.doublet
        else:
            print("ERROR")

        p = peak(x, p)
        xy_list[peakname_list[i]] = p
    
    return xy_list                    # Superposed y values.

# FWHM, area
def calc_fwhm(gamma, sigma):
  """
  Approximates the FWHM of a Voigt profile.

  Parameters
  ----------
  sigma : float
      Standard deviation of the Gaussian component.
  gamma : float
      HWHM of the Lorentzian component.

  Returns
  -------
  float
      Approximate FWHM of the Voigt profile.
  """
  fwhm_g = 2 * np.sqrt(2 * np.log(2)) * sigma
  fwhm_l = 2 * gamma
  return 0.5346 * fwhm_l + np.sqrt(0.2166 * fwhm_l**2 + fwhm_g**2)

def series_fwhm(param: pd.DataFrame) -> pd.Series:
    return param.apply(lambda row: calc_fwhm(row['gamma'], row['sigma']), axis=1)

def calc_area(x, y):
    #if is_descending(x=x):
    #    area = -1 * np.trapz(y, x)
    #else:
    #    area = np.trapz(y, x)
    #return area
    return abs(np.trapz(y, x))

def series_area(
    xy      : pd.DataFrame | None = None,
    x       : pd.Series    | np.ndarray | None = None,
    peaks   : pd.DataFrame | None = None,
    ) -> pd.Series:
    area_list = []
    if xy is not None:
        for c_name, c_data in xy.items():
            if c_name == "x":
                continue
            a = calc_area(xy["x"], c_data)
            area_list.append(a)
    
    elif x is not None and peaks is not None:
        for _, peak_ser in peaks.items():
            a = calc_area(x, peak_ser)
            area_list.append(a)

    return pd.Series(area_list)

def least_squares(
    xy          : pd.DataFrame | None, 
    model       : callable, 
    fitparam    : dict, 
    residual    = mdl.residual,
) -> scipy.optimize.OptimizeResult:
    """
    ## Wrapper of scipy.optimize.least_squares() via pd.Dataframe.
    - xy       : DataFrame including "x" and "y" columns.
    - model    : Function used for peak fitting.
    - fitparam : Dictionary including "guesses" and "boundaries" parameter keys.
    - residual : Function evaluating fitting residuals.
    """
    fit_args = (
        model,          # Fit model function
        xy.x.values,    # x *list* in fitting range (background subtracted).
        xy.y.values,    # y *list* in fitting range (background subtracted).
    )
    #print(fitparam["boundaries"])
    result = scipy.optimize.least_squares(
        # Minimizing residual function
        residual,                          # Function of residuals
        fitparam["guesses"],               # Initial guessing value of fitting
        bounds   = fitparam["boundaries"],  # Limit of fitting
        args     = fit_args,                # Arguments passed to residual functions 
        max_nfev = 1000,
        x_scale='jac',
        #xtol=1e-8,
        #ftol=1e-8,
    )
    if not result.success:
        print("ERROR")
        print(result)
        raise

    return result

def leastsq(
    xy          : pd.DataFrame  | None, 
    model       : callable, 
    fitparam    : pd.DataFrame, 
    residual                           = mdl.residual,
    x           : pd.Series     | None = None,
    y           : pd.Series     | None = None,
) -> scipy.optimize.OptimizeResult:
    if x is not None and y is not None:
        xy = pd.DataFrame({"x": x, "y": y})

    return least_squares(
        xy       = xy, 
        model    = model, 
        fitparam = extract_fitparams(fitparam),
        residual = residual
    )

def convert_peak_type_to_chunk_length(peaktype_list: list):
    """
    Convert a list of peak types to a list of the number of peaks.
    E.g. ["doublet", "doublet", "singlet"] to [6, 6, 4] 
    """

    rtn = []
    singlet_param_num = 4
    doublet_param_num = 6

    for pt in peaktype_list:
        if   pt == "singlet":
            rtn.append(singlet_param_num)
        elif pt == "doublet":
            rtn.append(doublet_param_num)
    return rtn

def separate_chunk(args, chunk_list) -> list:
    """
    Separating "args" according to "chunk_list".
    
    E.g. "args" such as
        [9.0e+01 1.0e-05 0.0e+00 1.0e-05 1.4e+02 1.0e-05 0.0e+00 1.0e-05 6.0e-01 1.0e+00]
    is separated to
        [[9.0e+01 1.0e-05 0.0e+00 1.0e-05], 
         [1.4e+02 1.0e-05 0.0e+00 1.0e-05 6.0e-01 1.0e+00]]
    by "chunk_list" of 
        [4, 6]
    """
    rtn = []
    begin = 0
    for size in chunk_list:
        rtn.append(args[begin : begin + size])
        begin += size
    return rtn

def build_fitmodel(peaktype_list: list) -> callable:
    """
    Building a function model by superposing fundamental functions (e.g. singlet and doublet of Voigt function).
    - chunk_list : List of the numbers of each peak parameter. (example: [6, 6, 4] means two doublet and one singlet)
    """

    chunk_length_list = convert_peak_type_to_chunk_length(peaktype_list)
    def fitmodel(x, args):  # not *args but args.
        # Separating args by each peak type (singlet or doublet).
        # The "chunk_list" is embedded to "built_model" function.
        params = separate_chunk(args, chunk_length_list)

        y = 0
        for p in params:            # "p" equals [x_pos, gamma, sigma, norm, (d_ratio), (d_shift)].
            L = len(p)
            if   L == SINGLET_PARAM_NUM:
                peak = mdl.singlet
            elif L == DOUBLET_PARAM_NUM:
                peak = mdl.doublet
            else:
                print("ERROR")

            y += peak(x, p)
        return y                    # Superposed y values.

    return fitmodel

def fitmodeling(fitparam: pd.DataFrame) -> callable:
    return build_fitmodel(peaktype_list=fitparam["peak_type"])

def convert_fitresult_to_df(fitresult: scipy.optimize.OptimizeResult, fitparam: pd.DataFrame) -> pd.DataFrame:
    """
    Converting fit-result parameters to pd.DataFrame for data readablity.
    """
    resultargs = fitresult.x
    e_fp = extract_fitparams(fitparam)
    ch_lis = convert_peak_type_to_chunk_length(e_fp["peak_type"])
    rows = separate_chunk(resultargs, ch_lis)

    col = []
    pn = e_fp["paramnum"]
    if   pn == SINGLET_PARAM_NUM:
        col = ["position", "gamma", "sigma", "norm"]
    elif pn == DOUBLET_PARAM_NUM:
        col = ["position", "gamma", "sigma", "norm", "d_ratio", "d_shift"]

    rtn = pd.DataFrame(rows, columns=col)

    rtn.insert(0, "peak_name",    fitparam["peak_name"].values)
    rtn.insert(1, "display_name", fitparam["display_name"].values)

    return rtn