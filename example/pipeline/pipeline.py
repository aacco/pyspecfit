import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pyspecfit as psf
import pybaselines


# ----------------------------------------------------------------------
# Load sample spectrum.
# ----------------------------------------------------------------------
df = pd.read_csv("sampledata/sampledata.csv")

# Create a figure consisting of one overview plot and two fitting results.
fig = plt.figure(figsize=(7, 7))
plt.rcParams["font.size"] = 9
gs = gridspec.GridSpec(2, 2)

# Create a Spectrum object from the loaded data.
spec = psf.Spectrum(xy=df)

# ----------------------------------------------------------------------
# Estimate the spectral baseline using the BEADS algorithm provided by
# pybaselines, then register it in the Spectrum object.
# ----------------------------------------------------------------------
baseline_fitter = pybaselines.Baseline(x_data=spec.data.x)
bkg2, params = baseline_fitter.beads(spec.data.y_raw, freq_cutoff=8e-5)

ax1 = fig.add_subplot(gs[0, :])  # 1行目全体を使う
ax1.plot(spec.data.x, spec.data.y_raw, label="Raw data", color="k")
ax1.plot(spec.data.x, bkg2, label="Baseline (Beads)", color="r")
ax1.set_xlabel("x")
ax1.set_ylabel("y")
ax1.legend()

spec.register_new_bg(bkg2, "pybaselines_beads")

# ----------------------------------------------------------------------
# Fit the reference peak to determine the spectral shift.
# ----------------------------------------------------------------------
fitparam_1 = pd.read_csv("./pipeline_fitparam_1.csv")
spec_1 = spec.xclip(clip_range=(320, 400), newfitparam=fitparam_1)
print(spec_1.all)
spec_1.fit()
spec_1.print_resultparam()
ax2 = fig.add_subplot(gs[1, 0])

ax2.plot(spec_1.data.x, spec_1.data.y_raw, label="Raw", color="k")
ax2.plot(spec_1.data.x, spec_1.data.y_bg, label="bg", color="r")
ax2.plot(spec_1.data.x, spec_1.data.y_fit, label="fit", color="b")
ax2.set_xlabel("x")
ax2.set_ylabel("y")
ax2.legend()

# Align the spectrum so that the fitted reference peak is located at x = 360.
spec.xshift(360 - spec_1.resultparam.position.values[0])

# ----------------------------------------------------------------------
# Fit the target spectral region using the shifted spectrum.
# ----------------------------------------------------------------------
fitparam_2 = pd.read_csv("./pipeline_fitparam_2.csv")
print(fitparam_2)
spec_2 = spec.xclip(clip_range=(50, 120), newfitparam=fitparam_2)
spec_2.fit()
spec_2.print_resultparam()

ax3 = fig.add_subplot(gs[1, 1])
ax3.plot(spec_2.data.x, spec_2.data.y_raw, label="Raw", color="k")
ax3.plot(spec_2.data.x, spec_2.data.y_bg, label="bg", color="r")
ax3.plot(spec_2.data.x, spec_2.data.y_fit, label="fit", color="b")
for col_name in spec_2.data.y_eles:
    ax3.fill_between(
        spec_2.data.x, 
        spec_2.data.y_eles[col_name] + spec_2.data.y_bg, 
        spec_2.data.y_bg, 
        alpha=0.25, label=col_name, linestyle="--", edgecolor="face")
ax3.legend()
ax3.set_xlabel("x")
ax3.set_ylabel("y")


spec_2.resultparam.to_csv(
    "log/resultparam.csv",
    index=False,
)
spec_2.save_data("log/xy.csv")

fig.savefig("log/pipeline_fit.png", dpi=300)
plt.show()
