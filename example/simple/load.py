import matplotlib.pyplot as plt
import pyspecfit

#BASE_PATH = "./example/simple/"

# Data loading #
test_peak = pyspecfit.Spectrum.load_csv("log/xy.csv")


# Plotting #
fig, ax = plt.subplots()
ax.plot(test_peak.x, test_peak.y_raw)
ax.plot(test_peak.x, test_peak.y_fit)
for col_name in test_peak.y_eles:
    ax.fill_between(
        test_peak.x, 
        test_peak.y_eles[col_name] + test_peak.y_bg, 
        test_peak.y_bg, 
        alpha=0.25
    )

plt.show()
