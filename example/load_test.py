import matplotlib.pyplot as plt
import pyspecfit

BASE_PATH = "./example/"

# Data loading #
test_peak = pyspecfit.Spectrum.load_csv(BASE_PATH + "log/xy.csv")


# Plotting #
fig, ax = plt.subplots()
ax.plot(test_peak.data.x, test_peak.data.y_raw)
ax.plot(test_peak.data.x, test_peak.data.y_fit)
for col_name in test_peak.data.y_eles:
    ax.fill_between(test_peak.data.x, test_peak.data.y_eles[col_name], alpha=0.25)

plt.show()