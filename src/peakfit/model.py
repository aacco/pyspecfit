import os
import json
import numpy as np
import pandas as pd
import scipy


def voigt(x, params):
    """
    ## params:
    - x_pos   : Center of Voigt line.
    - gamma   : Gamma of Lorentzian (equal to FWHM of Lorentzian).
    - sigma   : Sigma of Gaussian (equal to standard deviation of Gaussian).
    - norm    : Normalization (default = 1).
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
    ## params:
    - x_pos   : Center of Voigt line.
    - gamma   : Gamma of Lorentzian (equal to FWHM of Lorentzian).
    - sigma   : Sigma of Gaussian (equal to standard deviation of Gaussian).
    - norm    : Normalization (default = 1).
    """
    return voigt(x, params)

def doublet(x, params):
    """
    # Arguments
    x         : List of x within fit range.
    params: list
        - x_pos     : Center of main peak.
        - gamma     : Gamma of Lorentzian (equal to FWHM of Lorentzian).
        - sigma     : Sigma of Gaussian (equal to standard deviation of Gaussian).
        - norm      : Normalization (default = 1).
        - d_ratio   : Doublet ratio (ratio of intensity between main peak and sub peak).
        - d_shift   : Doublet shift (position shift between main peak and sub peak).
    """
    # Unpackking paramter to main-peak and sub-peak parameters.
    p_main = params[0:4]
    d_ratio, d_shift = params[4:6]

    main_peak = voigt(x, p_main)
    sub_params = [p_main[0] + d_shift, p_main[1], p_main[2], p_main[3] * d_ratio]
    sub_peak = voigt(x, sub_params)
    return main_peak + sub_peak

def residual(params, model_func, x, y):
    model = model_func(x, params)
    return y - model

def chunk_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]