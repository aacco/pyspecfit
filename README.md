# pyspecfit
Module for peak fitting in Python.

This utility module serves `Spectrum` class for easier hadling spectrum data in fitting curves.
Voigt profiles (singlet) or doublet are only supported for this module.

# Install
For development use, download and execute 
```shell
pip install -e .
```
in the same directory as `setup.py`.

# Usage
See also `/example` for demonstration code.

The minimum example code with raw data `df_raw` and fit parameters `df_fitparam`:
```python
import pyspecfit

# Create Spectrum instance 
test_peak = pyspecfit.Spectrum(xy=df_raw, fitparam=df_fitparam)

# Compute fitting 
test_peak.fit()

# Print fitting results
test_peak.print_resultparam()
```

After fitting, we can access plotting data with `.x`, `.y_raw` and `.y_fit` accesser as `pandas.Series`:
```python
import matplotlib as plt

# Plotting #
fig, ax = plt.subplots()
ax.plot(test_peak.x, test_peak.y_raw)
ax.plot(test_peak.x, test_peak.y_fit)
plt.show()
```

If some peaks are fitted at the same time, we can access each element of fitting using `.y_eles` accessor as `pandas.DataFrame`:
```python
# Plot all elements of peaks
for col_name in test_peak.y_eles:
    ax.plot(test_peak.x, test_peak.y_eles[col_name])
```

To save fitting data, use `to_csv` function of `pandas.DataFrame`:
```python
# Saving fit results #
test_peak.xy_all.to_csv("xy.csv", index=False)
test_peak.resultparam.to_csv("resultparam.csv", index=False)
```

If data were saved as csv file, `Spectrum` class can load the fitted data:
```python
test_peak = pyspecfit.Spectrum.load_csv("xy.csv")
```

These component accessors are shortcuts for `.data`, for example `.x` is a shortened expression of `.data.x`.

# Dependencies
 - [Numpy](https://www.numpy.org/)
 - [pandas](https://pandas.pydata.org/)
 - [SciPy](https://scipy.org/)
 - [Matplotlib](https://matplotlib.org/)

# License
MIT license