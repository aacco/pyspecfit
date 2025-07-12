import pandas as pd
import matplotlib.pyplot as plt
import pyspecfit as sf

BASE_PATH = "./example/"

# Data loading #
df_raw      = pd.read_csv(BASE_PATH + "sampledata/sampledata.csv")
df_fitparam = pd.read_csv(BASE_PATH + "fitparam.csv")


# Peakfit processing #
test_peak = sf.Spectrum(xy=df_raw, fitparam=df_fitparam)
test_peak.fit()
test_peak.print_resultparam()


# Saving fit results #
test_peak.data.xy_all.to_csv(BASE_PATH + "log/xy.csv", index=False)
test_peak.resultparam.to_csv(BASE_PATH + "log/resultparam.csv", index=False)


# Plotting #
fig, ax = plt.subplots()
ax.plot(test_peak.data.x, test_peak.data.y_raw)
ax.plot(test_peak.data.x, test_peak.data.y_fit)
for col_name in test_peak.data.y_eles:
    ax.fill_between(test_peak.data.x, test_peak.data.y_eles[col_name], alpha=0.25)

plt.show()