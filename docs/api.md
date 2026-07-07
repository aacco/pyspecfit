# API Reference

This document describes the user-facing API of **pyspecfit**.

Most workflows should use the `Spectrum` class.  
`xySeries` and `bgSeries` are exposed, but they are mainly used internally by `Spectrum`.

---

# Import

```python
import pyspecfit as psf
```

Main classes:

```python
psf.Spectrum
psf.xySeries
psf.bgSeries
```

---

# Spectrum

`Spectrum` is the main class for a complete peak-fitting session.

It manages

- raw spectral data,
- fitting parameters,
- registered backgrounds,
- peak fitting,
- fitted curves,
- optimized parameters.

---

## Constructor

```python
sp = psf.Spectrum(
    x=None,
    raw=None,
    xy=None,
    sanitized=False,
    fitparam=None,
    loadpath=None,
)
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `x` | `pandas.Series` or `numpy.ndarray` | `None` | x-axis data. Use together with `raw`. |
| `raw` | `pandas.Series` or `numpy.ndarray` | `None` | Raw intensity data. Use together with `x`. |
| `xy` | `pandas.DataFrame` | `None` | Raw spectrum as a DataFrame. If `sanitized=False`, the first column is used as x and the second column as raw intensity. |
| `sanitized` | `bool` | `False` | If `True`, `xy` is treated as an already formatted `xySeries`-style MultiIndex DataFrame. |
| `fitparam` | `pandas.DataFrame` | `None` | Fitting parameter table. Only rows with `is_used == True` are used. |
| `loadpath` | `str` | `None` | Path to a saved `xy_all` CSV file. Usually use `Spectrum.load_csv()` instead. |

---

## Common initialization patterns

### From a raw spectrum DataFrame

```python
sp = psf.Spectrum(
    xy=df_raw,
    fitparam=df_fitparam,
)
```

`df_raw` should contain at least two columns.  
The first column is interpreted as x, and the second column as raw intensity.

---

### From x and raw arrays

```python
sp = psf.Spectrum(
    x=x,
    raw=y,
    fitparam=df_fitparam,
)
```

---

### From a saved fitted spectrum

```python
sp = psf.Spectrum.load_csv("xy.csv")
```

Use this for CSV files exported from `sp.save_data()` or `sp.data.xy_all.to_csv()`.

---

## set_fitparam()

Set or replace the fitting parameter table.

```python
sp.set_fitparam(fitparam)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `fitparam` | `pandas.DataFrame` | Fitting parameter table. Rows with `is_used == True` are retained. |

### Returns

```python
None
```

### Note

If you replace `fitparam` after creating a `Spectrum`, confirm that the fitting model is consistent with the new table before fitting.

---

## register_new_bg()

Register a background spectrum.

```python
sp.register_new_bg(
    bg_data,
    bg_name,
)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `bg_data` | `numpy.ndarray`, `pandas.Series`, or `bgSeries` | Background intensity data. |
| `bg_name` | `str` | Name used for the background column. |

### Returns

```python
None
```

### Behavior

The registered background is stored in `sp.data` under the `bg` column level.

Conceptually:

```text
bg
 └── bg_name
```

The total background `sp.data.y_bg` is updated automatically as the sum of registered background components.

### Example

```python
baseline = pybaselines.Baseline(x_data=sp.data.x)

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

## fit_background()

Estimate and register a background using an external function.

```python
bg_result = sp.fit_background(
    func,
    bg_name=None,
    xy=None,
    args=(),
    kwargs={},
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `func` | `callable` | required | Function called as `func(xy, *args, **kwargs)`. |
| `bg_name` | `str` | `None` | Name used when registering the background. |
| `xy` | `pandas.DataFrame` | `None` | Data passed to `func`. If `None`, a DataFrame with `x` and `y` is created from `sp.data.x` and `sp.data.y_raw`. |
| `args` | `tuple` | `()` | Positional arguments passed to `func`. |
| `kwargs` | `dict` | `{}` | Keyword arguments passed to `func`. |

### Returns

The object returned by `func`.

### Note

For most users, direct use of `register_new_bg()` is simpler and clearer.

---

## fit()

Perform nonlinear peak fitting.

```python
sp.fit(
    xrange=None,
    fitparam=None,
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `xrange` | `tuple` | `None` | Optional fitting range as `(xmin, xmax)`. |
| `fitparam` | `pandas.DataFrame` | `None` | Optional fitting parameter table. If provided, it replaces the current `sp.fitparam` before fitting. |

### Returns

```python
None
```

### Behavior

If a background is registered, fitting is performed on

```python
sp.data.y_raw_without_bg
```

Otherwise, fitting is performed on

```python
sp.data.y_raw
```

After fitting, `sp.data.y_fit` is updated as the fitted peaks plus the registered background.

### Updated attributes

```python
sp.optimize_result
sp.resultparam
sp.data.y_fit
sp.data.y_eles
```

`sp.resultparam` also receives calculated values such as `FWHM` and `area`.

### Example

```python
sp.fit()
```

With a fitting range:

```python
sp.fit(
    xrange=(280, 295),
)
```

---

## print_resultparam()

Print optimized fitting parameters.

```python
sp.print_resultparam()
```

### Returns

```python
None
```

---

## xclip()

Create a new `Spectrum` object from a selected x range.

```python
sp_sub = sp.xclip(
    clip_range,
    reset_index=True,
    newfitparam=None,
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `clip_range` | `tuple` | required | x range as `(xmin, xmax)`. |
| `reset_index` | `bool` | `True` | If `True`, reset the index of the clipped data. |
| `newfitparam` | `pandas.DataFrame` | `None` | Optional fitting parameter table for the returned `Spectrum`. |

### Returns

```python
Spectrum
```

### Note

`xclip()` returns a new `Spectrum` object.  
The original object is not modified.

---

## xshift()

Shift the x-axis.

```python
sp.xshift(shift)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `shift` | `float` | Value added to the x-axis. |

### Returns

```python
Spectrum
```

The current object is modified and returned.

---

## save_data()

Save the complete processed spectrum.

```python
sp.save_data(path)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `path` | `str` | Output CSV path. |

### Returns

```python
None
```

This saves `sp.data.xy_all` with `index=False`.

---

## load_csv()

Load a saved processed spectrum.

```python
sp = psf.Spectrum.load_csv(path)
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `path` | `str` | Path to a CSV file exported from `save_data()` or `sp.data.xy_all.to_csv()`. |

### Returns

```python
Spectrum
```

---

# Spectrum properties

The following shortcuts are available.

| Property | Description |
|---|---|
| `sp.data` | Underlying `xySeries` object |
| `sp.xy_all` or `sp.all` | Complete processed spectrum |
| `sp.x` | x-axis |
| `sp.y_raw` or `sp.y` | Raw intensity |
| `sp.y_bg` or `sp.bg` | Total background |
| `sp.y_raw_without_bg` | Background-subtracted raw intensity |
| `sp.y_fit` | Fitted spectrum |
| `sp.y_eles` | Fitted peak components |
| `sp.resultparam` | Optimized fitting parameters |
| `sp.residual` | Difference between raw and fitted spectrum |
| `sp.rms` | Root mean squared residual |

---

# xySeries

`xySeries` stores numerical spectral data.

Normally, users access it through

```python
sp.data
```

rather than creating it directly.

---

## Constructor

```python
data = psf.xySeries(
    x=None,
    raw=None,
    loaded_data=None,
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `x` | `pandas.Series` or `numpy.ndarray` | `None` | x-axis data. Use together with `raw`. |
| `raw` | `pandas.Series` or `numpy.ndarray` | `None` | Raw intensity data. Use together with `x`. |
| `loaded_data` | `pandas.DataFrame` | `None` | Already formatted MultiIndex DataFrame. |

---

## Data structure

`xySeries` stores data in a MultiIndex `pandas.DataFrame`.

Conceptually:

```text
base
 ├── x
 ├── y_raw
 ├── y_bg
 └── y_fit

bg
 ├── background_1
 └── background_2

peak
 ├── peak_1
 └── peak_2
```

---

## Common properties

| Property | Description |
|---|---|
| `xy_all` or `all` | Complete MultiIndex DataFrame |
| `x` | x-axis |
| `y_raw` or `raw` | Raw intensity |
| `y_bg` or `bg` | Total background |
| `y_raw_without_bg` | Raw intensity minus background |
| `y_fit` or `fit` | Fitted spectrum |
| `y_eles` | Fitted peak components |
| `bases` | DataFrame under the `base` column level |
| `bgs` | DataFrame under the `bg` column level |
| `peaks` | DataFrame under the `peak` column level |
| `residual` | Raw intensity minus fitted spectrum |

---

## Common methods

### to_df()

Return the complete data table.

```python
df = sp.data.to_df()
```

### xshift()

Shift x-axis values.

```python
sp.data.xshift(shift)
```

### update_bg_element()

Add or update one background component.

```python
sp.data.update_bg_element(
    ser,
    column_name,
)
```

### update_peak_element()

Add or update one peak component.

```python
sp.data.update_peak_element(
    ser,
    column_name,
)
```

These methods are usually called through `Spectrum`.

---

# bgSeries

`bgSeries` is a lightweight wrapper for background estimation results.

Most users do not need to instantiate it directly, because `register_new_bg()` also accepts array-like background data.

---

## Constructor

```python
bg_result = psf.bgSeries(
    bg,
    index=None,
    other=None,
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `bg` | `pandas.Series` or `numpy.ndarray` | required | Background intensity data. |
| `index` | `pandas.Series` or `numpy.ndarray` | `None` | Optional index for the background data. If provided, `bg` is converted to a `pandas.Series` with this index. |
| `other` | `dict` | `None` | Optional metadata or additional results from background estimation. |

---

## Properties

| Property | Description |
|---|---|
| `bg` | Background intensity data |
| `index` | Index passed at construction |
| `has_index` | Whether an index was provided |
| `other` | Additional metadata |
| `has_other` | Whether metadata were provided |

---

# Minimal example

```python
import pandas as pd
import matplotlib.pyplot as plt
import pybaselines
import pyspecfit as psf

df_raw = pd.read_csv("sampledata/sampledata.csv")
df_fitparam = pd.read_csv("fitparam.csv")

sp = psf.Spectrum(
    xy=df_raw,
    fitparam=df_fitparam,
)

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

sp.fit()

sp.save_data("xy.csv")

sp.resultparam.to_csv(
    "resultparam.csv",
    index=False,
)
```

---

# Recommended public API

For typical use, rely on the following API.

```python
psf.Spectrum
sp.register_new_bg()
sp.fit()
sp.print_resultparam()
sp.data
sp.resultparam
sp.save_data()
psf.Spectrum.load_csv()
```