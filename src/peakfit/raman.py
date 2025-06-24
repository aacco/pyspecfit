import numpy as np
import pandas as pd

from . import common as cmn

RAMAN   = "Raman"
RAMAN_PARAMS = {
    "xlabel": r"$Raman shift \left[cm^{-1}\right]$",
    "ylabel": "Intensity [cps]",
}
SILICON_PEAK_POS    = 520
SILICON_PEAK_RANGE  = [510, 530]

def read_csv(path: str) -> pd.DataFrame:
    col_name = ["x", "y", "additional_column"]  # Fomal and temporary column name to open irregular CSV file
    _df = pd.read_csv(path, names=col_name, encoding="shift-jis")  # Use shift-jis because Raman CSV contains Japanese charactors.
    df = _df.fillna('')  # Fill nan by blank string, just to be safe.

    num_only_bool_index = df["x"].apply(cmn.is_only_floats)  # eliminating head data and exstracting raw data of Raman
    num_df = df[num_only_bool_index].dropna(how="all")
    num_df = num_df.drop("additional_column", axis=1)  # eliminating "additional_column".
    num_df = num_df.astype(float)  # Convert str to float.
    return num_df.reset_index().drop("index", axis=1)  # Reset index; starting with 0.

def calibrate_by_Si_peak(xy):
    i_Si_min = np.where(xy["Kayser"] >= SILICON_PEAK_RANGE[0])[0][0]
    i_Si_max = np.where(xy["Kayser"] <= SILICON_PEAK_RANGE[1])[0][-1]

    #print(i_Si_max)
    #print(i_Si_min)
    xy_trimed = np.array([xy["Kayser"][i_Si_min:i_Si_max], xy["Intensity"][i_Si_min:i_Si_max]])
    #i_p, _ = scipy.signal.find_peaks(xy_trimed[1], prominence=(FIND_PEAKS_PROMINENCE_MIN, None))
    i_p = np.argmax(xy_trimed[1])
    #print(i_p)
    raw_silicon_peak_pos = xy_trimed[0][i_p]
    return np.array([xy[0] + (SILICON_PEAK_POS - raw_silicon_peak_pos), xy[1]])

def calibrate_Si_position(xy):
    return calibrate_by_Si_peak(xy)