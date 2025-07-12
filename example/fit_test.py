import pyspecfit.common as cmn
import pandas as pd
import matplotlib.pyplot as plt

df_raw      = pd.read_csv("./example/sampledata/sampledata.csv")
df_fitparam = pd.read_csv("./example/fitparam.csv")

fitmodel = cmn.fitmodeling(df_fitparam)

# Fitting #
f_output = cmn.leastsq(xy=df_raw, model=fitmodel, fitparam=df_fitparam)

# Results parsing #
df_resparam = cmn.convert_fitresult_to_df(f_output, df_fitparam)

y_fit   = fitmodel(x=df_raw.x.values, args=f_output.x)
xy_eles = cmn.build_peak_elements(df_raw.x.values, f_output, df_fitparam)
# y-axis data by eliminating "x" column (= screening by "peak_name" column) from xy_eles.
y_eles  = xy_eles[df_fitparam["peak_name"]]

df_resparam['FWHM'] = cmn.series_fwhm(df_resparam)
df_resparam['area'] = cmn.series_area(xy_eles)

print(df_resparam.drop(columns=["display_name"]))

# Plotting #
fig, ax = plt.subplots()
ax.plot(df_raw.x, df_raw.y)
ax.plot(df_raw.x, y_fit)
for col_name in y_eles:
    ax.fill_between(df_raw.x, y_eles[col_name], alpha=0.25)

df_resparam.to_csv("./example/log/fitresult.csv")

plt.show()