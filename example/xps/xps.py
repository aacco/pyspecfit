import pandas as pd
import matplotlib.pyplot as plt
import pyspecfit
import pyspecfit.xps as xps


path_fitparam   = "./example/xps/C1s.csv"
c1s_path        = "./example/xps/sampledata.csv"

df_raw          = xps.read_csv(c1s_path, dataframe=True)
df_fitparam     = pd.read_csv(path_fitparam)

C1s = pyspecfit.Spectrum(xy=df_raw, fitparam=df_fitparam)

C1s.fit_background(
    func=xps.linear_and_shirley,
    kwargs={
        "range_linear"  : (286, 297),
        "range_shirley" : (278, 290),
    }
)

C1s.fit(xrange=(278, 290))
C1s.print_resultparam()


# Plotting #
fig, ax = plt.subplots(2, 1, sharex="all")

## Residual window
ax[0].axhline(0, color="k")
ax[0].plot(C1s.x, C1s.residual)
ax[0].text(0.01, 0.98, f"Residual\nRMS={C1s.rms}",
            horizontalalignment='left',
            verticalalignment='top', 
            transform=ax[0].transAxes)

## Spectrum window
ax[1].plot(C1s.data.x, C1s.data.y_bg)
ax[1].fill_between(C1s.data.x, C1s.data.y_fit, C1s.data.y_bg, alpha=0.25)
kwargs = {
    "color" : "k",
    "marker": ".",
    "s"  : 4,
}
ax[1].scatter(C1s.data.x, C1s.data.y_raw, **kwargs)
ax[1].invert_xaxis()


plt.show()