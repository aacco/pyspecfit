import json
import numpy as np

class Peak:
    """
    # Peak class
    An instance of this Peak class has these properties:
    - name: str
    - display_name: str
    - x: Series
    - y: Series
    - peak_number
    - (is_singlet: bool)
    - (is_doublet: bool)
    - is_used: bool
    - fit_cond
        - bg(?)
            - start
            - end
        - fit
            - start
            - end
        - init: 1x6-array-like: float
            - position      
            - sigma         
            - gamma         
            - norm          
            - doublet_shift 
            - doublet_ratio 
        - is_hold: 1x6-array-like: bool
            - position      
            - sigma         
            - gamma         
            - norm          
            - doublet_shift 
            - doublet_ratio 
        - bounds: 2x6-array-like: float
            - position      : upper/lower
            - sigma         : upper/lower
            - gamma         : upper/lower
            - norm          : upper/lower
            - doublet_shift : upper/lower
            - doublet_ratio : upper/lower
    - fit_result: 1x6-array-like
        - position      
        - sigma         
        - gamma         
        - norm          
        - doublet_shift 
        - doublet_ratio 
    """

    def __init__(self):
        pass

    def read_json(path: str):
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
                parse_result["chem_shifts"].append(chem_shift_key)
                # Initial guess loading
                chem_shift_peak = peaks[chem_shift_key]
                pr = parse_result[chem_shift_key] = {}  # Append new chemical shift key

                param_keys = [posi, gamm, sigm, norm]
                if d_ra in chem_shift_peak:
                    param_keys.append(d_ra)
                    param_keys.append(d_sh)

                _params_init = []
                for p in param_keys:
                    _params_init.append(chem_shift_peak[p][init])
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
                        _min = xps.parse_null(chem_shift_peak[i_p][lo], "min")
                        _max = xps.parse_null(chem_shift_peak[i_p][up], "max")
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

        return range_linear, range_peak, parse_result

    def fit(self):
        pass