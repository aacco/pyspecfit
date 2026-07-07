import pandas as pd
import matplotlib.pyplot as plt
import pybaselines
import pyspecfit as psf

# Load spectrum
df_raw = pd.read_csv("sampledata/sampledata.csv")
df_fitparam = pd.read_csv("fitparam.csv")

# Create Spectrum object
sp = psf.Spectrum(
    xy=df_raw,
    fitparam=df_fitparam,
)

# Estimate background
baseline = pybaselines.Baseline(
    x_data=sp.data.x
)

bg, _ = baseline.beads(
    sp.data.y_raw,
    freq_cutoff=1e-4,
)

sp.register_new_bg(
    bg,
    "pybaselines_beads",
)

# Peak fitting
sp.fit()

# Print optimized parameters
sp.print_resultparam()

# Plot results
fig, ax = plt.subplots()

ax.plot(sp.data.x, sp.data.y_raw, label="Raw")
ax.plot(sp.data.x, sp.data.y_bg, label="Background")
ax.plot(sp.data.x, sp.data.y_fit, label="Fit")

for name, peak in sp.data.y_eles.items():
    ax.fill_between(
        sp.data.x,
        peak + sp.data.y_bg,
        sp.data.y_bg,
        alpha=0.3,
        label=name,
    )

ax.legend()

#fig.savefig("simple.png", dpi=300)

# Save results
## resultparam.csv is saved in the log folder
sp.resultparam.to_csv("log/resultparam.csv", index=False)
## xy.csv is saved in the log folder
sp.save_data("log/xy.csv")

plt.show()