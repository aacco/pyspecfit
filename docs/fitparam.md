# Fitting Parameter Table

`Spectrum` uses a CSV file to define peak models and fitting parameters.

Each row represents one peak model, and each column defines a fitting parameter, optimization constraint, or fitting range. The table is read during the initialization of `Spectrum` and is used to construct the fitting model.

---

# Example

```csv
peak_name,display_name,is_used,peak_type,...
peak_a1,Peak $A_1$,True,singlet,...
peak_b2,Peak $B_2$,True,doublet,...
```

Each row corresponds to one peak model.

---

# Required Columns

The following columns are required to construct a fitting model.

## Peak definition

| Column | Description |
|---|---|
| `peak_name` | Internal identifier of the peak. Used when storing fitted peak components. |
| `display_name` | Name displayed in plots and exported fitting results. |
| `is_used` | Indicates whether the peak is included in the fitting model. |
| `peak_type` | Peak model. Supported values are `singlet` and `doublet`. |

---

## Peak parameters

The following parameter groups are required for both `singlet` and `doublet` peaks.

### Peak position

| Column | Description |
|---|---|
| `position_guess` | Initial value. |
| `position_limit_lower` | Lower optimization bound. |
| `position_limit_upper` | Upper optimization bound. |
| `position_hold` | If `True`, the parameter is fixed during optimization. |

---

### Peak intensity

| Column | Description |
|---|---|
| `norm_guess` | Initial value. |
| `norm_limit_lower` | Lower optimization bound. |
| `norm_limit_upper` | Upper optimization bound. |
| `norm_hold` | If `True`, the parameter is fixed during optimization. |

---

### Lorentzian width

| Column | Description |
|---|---|
| `gamma_guess` | Initial value. |
| `gamma_limit_lower` | Lower optimization bound. |
| `gamma_limit_upper` | Upper optimization bound. |
| `gamma_hold` | If `True`, the parameter is fixed during optimization. |

---

### Gaussian width

| Column | Description |
|---|---|
| `sigma_guess` | Initial value. |
| `sigma_limit_lower` | Lower optimization bound. |
| `sigma_limit_upper` | Upper optimization bound. |
| `sigma_hold` | If `True`, the parameter is fixed during optimization. |

---

# Additional Columns for Doublet Peaks

When

```text
peak_type = doublet
```

the following columns are also required.

### Intensity ratio

| Column | Description |
|---|---|
| `d_ratio_guess` | Initial value. |
| `d_ratio_limit_lower` | Lower optimization bound. |
| `d_ratio_limit_upper` | Upper optimization bound. |
| `d_ratio_hold` | If `True`, the parameter is fixed during optimization. |

---

### Energy separation

| Column | Description |
|---|---|
| `d_shift_guess` | Initial value. |
| `d_shift_limit_lower` | Lower optimization bound. |
| `d_shift_limit_upper` | Upper optimization bound. |
| `d_shift_hold` | If `True`, the parameter is fixed during optimization. |

These columns are ignored when `peak_type` is `singlet`.

---

# Optional Columns

The following columns are not required to construct the fitting model, but are commonly used by analysis scripts.

## Background region

| Column | Description |
|---|---|
| `bg_start` | Beginning of the background region. |
| `bg_end` | End of the background region. |

These values are typically passed to background estimation functions such as

```python
sp.fit_background(...)
```

---

## Fitting region

| Column | Description |
|---|---|
| `fit_start` | Beginning of the fitting region. |
| `fit_end` | End of the fitting region. |

These values can be used when specifying

```python
sp.fit(
    xrange=(fit_start, fit_end)
)
```

---

# Peak Models

## singlet

Represents a single Voigt peak.

---

## doublet

Represents two coupled Voigt peaks.

The two peaks share the same peak widths, while the intensity ratio and energy separation are controlled by the corresponding doublet parameters.

---

# Parameter Constraints

Most fitting parameters are represented by four columns.

| Suffix | Description |
|---|---|
| `_guess` | Initial value |
| `_limit_lower` | Lower optimization bound |
| `_limit_upper` | Upper optimization bound |
| `_hold` | Whether the parameter is fixed |

If `*_hold` is `True`, the parameter is excluded from optimization and remains fixed at its initial value.

---

# Unused Peaks

Rows with

```text
is_used = False
```

are excluded from the fitting model.

This allows peaks to be enabled or disabled without removing rows from the parameter table.

---

# Typical Workflow

```python
fitparam = pd.read_csv("fitparam.csv")

sp = psf.Spectrum(
    xy=df_raw,
    fitparam=fitparam,
)

sp.fit_background(
    ...
)

sp.fit(
    xrange=(
        fitparam["fit_start"].iloc[0],
        fitparam["fit_end"].iloc[0],
    ),
)
```

The fitting parameter table is commonly used to define both the fitting model and the fitting region.

---

# Interpretation of the Parameter Table

During initialization, `Spectrum` interprets the parameter table and constructs the fitting model.

Conceptually,

```text
fitparam.csv
      │
      ▼
Peak model
      │
      ▼
Optimization
      │
      ▼
resultparam
```

The optimized parameters are stored in `Spectrum.resultparam`, while the fitted spectrum and individual peak components are stored in `Spectrum.data`.

---

# Recommendations

The following practices are generally recommended.

- Choose physically reasonable initial values whenever possible.
- Specify optimization bounds for free parameters.
- Fix parameters that are known a priori.
- Keep fitting conditions in the parameter table rather than modifying analysis scripts.