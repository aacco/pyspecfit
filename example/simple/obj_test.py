import pandas as pd
import matplotlib.pyplot as plt
import pybaselines
import pyspecfit as sf

BASE_PATH = "./example/simple/"

# Data loading #
df_raw      = pd.read_csv(BASE_PATH + "sampledata/sampledata.csv")
df_fitparam = pd.read_csv(BASE_PATH + "fitparam.csv")


# Peakfit processing #
test_peak = sf.Spectrum(xy=df_raw, fitparam=df_fitparam)

# Background estimation #
baseline_fitter = pybaselines.Baseline(x_data=test_peak.data.x)
bkg2, params = baseline_fitter.beads(test_peak.data.y_raw, freq_cutoff=0.0001)
test_peak.register_new_bg(bkg2, "pybaselines_beads")

# Fitting #
test_peak.fit()
test_peak.print_resultparam()


# Saving fit results #
test_peak.data.xy_all.to_csv(BASE_PATH + "log/xy.csv", index=False)
test_peak.resultparam.to_csv(BASE_PATH + "log/resultparam.csv", index=False)


# Plotting #
fig, ax = plt.subplots()
ax.plot(test_peak.x, test_peak.y_raw, label="raw data", color="black")
ax.plot(test_peak.x, test_peak.y_bg, label="background", color="red")
ax.plot(test_peak.x, test_peak.y_fit, label="fit", color="blue")
for col_name in test_peak.y_eles:
    ax.fill_between(test_peak.x, test_peak.y_eles[col_name] + test_peak.y_bg, test_peak.y_bg, alpha=0.25)

plt.legend()
plt.show()
