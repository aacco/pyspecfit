import pandas as pd

from . import common as cmn

XRD_OOP = "2t-t"
XRD_OOP_PARAMS = {
    "xlabel": r"$2\theta / \theta \; \left[deg\right]$",
    "ylabel": "Intensity [cps]",
}
XRD_FTF = "2t"
XRD_FTF_PARAMS = {
    "xlabel": r"$2\theta \; \left[deg\right]$",
    "ylabel": "Intensity [cps]",
}
XRD_IP  = "2tc-p"
XRD_IP_PARAMS = {
    "xlabel": r"$2\theta \chi / \phi \; \left[deg\right]$",
    "ylabel": "Intensity [cps]",
}
XRR     = "XRR"
XRR_PARAMS = {
    "xlabel": r"$2\theta \; \left[deg\right]$",
    "ylabel": "Intensity [cps]",
}

def read_text(path: str) -> pd.DataFrame:
    col_name = ["x", "y"]
    _df = pd.read_table(path, delimiter=" ", names=col_name, encoding="shift-jis")  # Please select proper delimiter as you chose in converting rasx files.
    bi = _df["x"].apply(cmn.is_only_floats)  # gain bool index (bi) of raw data area.
    df = _df[bi]  # raw data table.
    df_float = df.astype(float)  # Convert str to float.
    #xy = num_df.to_numpy()  # Convert pandas.dataframe to numpy.ndarray.
    #xy = xy.T  # Transposition of xy
    return df_float

def load_fitparam(path: str):
    return