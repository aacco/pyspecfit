
import pyspecfit
import pyspecfit.common as cmn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df_p = pd.read_csv("./python/project/test/fit_test/sampledata/trueparam.csv")
#print(df_p.values)
__params = df_p[["position_guess", "gamma_guess", "sigma_guess", "norm_guess", "d_ratio_guess", "d_shift_guess"]].values
_params = __params.reshape(__params.size)  # 1D-array
params = _params[~np.isnan(_params)]

m = cmn.build_fitmodel(df_p.peak_type.values)
x = np.arange(500, 4000, 1) / 10
y_true = m(x=x, args=params)

thermal_noise = np.random.normal(0, 0.01, len(x))
y = y_true + thermal_noise

fig, ax = plt.subplots()
ax.plot(x, y)

df_xy = pd.DataFrame({"x": x, "y": y})
print(df_xy)
df_xy.to_csv("./python/project/test/fit_test/sampledata/sampledata.csv", index=False)
plt.show()