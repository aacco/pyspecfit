# Background Estimation

`pyspecfit` treats background estimation as a modular step separated from peak fitting.

Backgrounds can be registered in two ways:

1. Use an external algorithm, such as `pybaselines`.
2. Use the built-in XPS background utilities in `pyspecfit.xps`.

---

# Basic Concept

A fitting workflow usually consists of:

```text
Raw spectrum
      │
      ▼
Background estimation
      │
      ▼
Register background
      │
      ▼
Peak fitting
```

Once a background is registered, `Spectrum.fit()` performs fitting on the background-subtracted spectrum.

Internally:

```text
y_raw - y_bg
      │
      ▼
peak fitting
      │
      ▼
y_fit = fitted peaks + y_bg
```

Therefore, `sp.data.y_fit` represents the fitted curve on the original raw-spectrum scale.

---

# Registering a Background Directly

The simplest way is to estimate a background externally and register it manually.

```python
sp.register_new_bg(
    background,
    "background_name",
)
```

## Parameters

| Parameter | Description |
|---|---|
| `background` | Array-like background intensity data |
| `background_name` | Name used to store the background in `sp.data` |

Example:

```python
import pybaselines

baseline = pybaselines.Baseline(
    x_data=sp.data.x,
)

bg, _ = baseline.beads(
    sp.data.y_raw,
    freq_cutoff=1e-4,
)

sp.register_new_bg(
    bg,
    "pybaselines_beads",
)
```

---

# Built-in XPS Background: linear_and_shirley

`pyspecfit` also provides XPS-oriented background utilities.

The most typical function is:

```python
psf.xps.linear_and_shirley
```

This function combines a linear background and a Shirley-type background.

It is useful for XPS spectra where a simple constant or linear background is insufficient.

---

# Using fit_background()

`Spectrum.fit_background()` estimates a background using a function and registers the result.

```python
sp.fit_background(
    func=psf.xps.linear_and_shirley,
    bg_name="shirley",
    kwargs={
        "range_linear": range_linear,
        "range_shirley": range_shirley,
    },
)
```

## Parameters

| Parameter | Description |
|---|---|
| `func` | Background estimation function |
| `bg_name` | Name assigned to the registered background |
| `kwargs` | Keyword arguments passed to the background function |

---

# Example: XPS Shirley Background

```python
import pandas as pd
import pyspecfit as psf

df_raw = pd.read_csv("Zr3d.csv")
fitparam = pd.read_csv("Zr3d_fitparam.csv")

sp = psf.Spectrum(
    xy=df_raw,
    fitparam=fitparam,
)

range_linear = (
    fitparam["bg_start"].iloc[0],
    fitparam["bg_end"].iloc[0],
)

range_shirley = (
    fitparam["fit_start"].iloc[0],
    fitparam["fit_end"].iloc[0],
)

sp.fit_background(
    func=psf.xps.linear_and_shirley,
    bg_name="shirley",
    kwargs={
        "range_linear": range_linear,
        "range_shirley": range_shirley,
    },
)

sp.fit(
    xrange=range_shirley,
)

sp.print_resultparam()
```

---

# Example: Energy Calibration Using C 1s

For XPS analysis, a common workflow is to fit the C 1s peak first, then shift other spectra using the fitted C 1s position.

```python
fitparam_C1s = pd.read_csv("C1s.csv")

sp_C1s = psf.Spectrum(
    xy=df_C1s,
    fitparam=fitparam_C1s,
)

range_shirley = (
    fitparam_C1s["fit_start"].iloc[0],
    fitparam_C1s["fit_end"].iloc[0],
)

sp_C1s.fit_background(
    func=psf.xps.linear_and_shirley,
    bg_name="shirley",
    kwargs={
        "range_linear": (
            fitparam_C1s["bg_start"].iloc[0],
            fitparam_C1s["bg_end"].iloc[0],
        ),
        "range_shirley": range_shirley,
    },
)

sp_C1s.fit(
    xrange=range_shirley,
)

C1s_pos = sp_C1s.resultparam["position"].iloc[0]
```

Then another spectrum can be shifted before fitting:

```python
sp_Zr3d = psf.Spectrum(
    xy=df_Zr3d,
    fitparam=fitparam_Zr3d,
)

sp_Zr3d.xshift(
    284.6 - C1s_pos,
)
```

---

# Multiple Background Components

`xySeries` can store multiple background components.

Conceptually:

```text
bg
 ├── shirley
 ├── pybaselines_beads
 └── custom
```

The total background is stored as:

```python
sp.data.y_bg
```

and is calculated from registered background components.

---

# Plotting with Background

For XPS spectra, it is often useful to plot peak components on top of the background.

```python
fig, ax = plt.subplots()

ax.scatter(
    sp.data.x,
    sp.data.y_raw,
    color="k",
    s=4,
    label="Raw",
)

ax.plot(
    sp.data.x,
    sp.data.y_bg,
    label="Background",
)

ax.plot(
    sp.data.x,
    sp.data.y_fit,
    label="Fit",
)

for name, peak in sp.data.y_eles.items():
    ax.fill_between(
        sp.data.x,
        peak + sp.data.y_bg,
        sp.data.y_bg,
        alpha=0.3,
        label=name,
    )

ax.invert_xaxis()
ax.legend()
plt.show()
```

---

# Recommended Usage

For general spectra:

```python
sp.register_new_bg(
    background,
    "background_name",
)
```

For XPS spectra:

```python
sp.fit_background(
    func=psf.xps.linear_and_shirley,
    bg_name="shirley",
    kwargs={
        "range_linear": range_linear,
        "range_shirley": range_shirley,
    },
)
```

---

# Summary

`pyspecfit` supports two background workflows:

- **External background estimation**, using packages such as `pybaselines`.
- **Built-in XPS background estimation**, using utilities such as `psf.xps.linear_and_shirley`.

Both workflows register the resulting background into `Spectrum.data`, after which peak fitting proceeds in the same way.