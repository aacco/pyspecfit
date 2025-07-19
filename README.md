# pyspecfit
Module for peak fitting in Python.

This utility module serves `Spectrum` class for easier hadling spectrum data in 
fitting curves.Voigt profiles (singlet) or doublet are only supported for this 
module.

# Install
For development use, download and execute 
```shell
pip install -e .
```
in the same directory as `setup.py`.

# Usage
## Flow
1. Create `Spectrum` object by registering raw data and fitting conditions.
2. (Optional) Estimate background of spectrum.
3. Fit with parameters.
4. Plot with accessors.
5. Save the results and load it.

See also `example/` for more demonstration code.


## 1. Create `Specturm` object
The minimum example code crating object with raw data `df_raw` and fit parameters 
`df_fitparam`:
```python
import pandas as pd
import pyspecfit

df_raw      = pd.read_csv("./example/sampledata/sampledata.csv")
df_fitparam = pd.read_csv("./example/fitparam.csv")

# Create Spectrum instance 
test_peak = pyspecfit.Spectrum(xy=df_raw, fitparam=df_fitparam)
```
NOTICE:

The raw data `df_raw` must have at least two columns named `x` and `y` (or `y_raw`).
The fitting parameters `df_fitparam` must incluede following columns: peak_name, 
display_name, is_used, peak_type, bg_start, bd_end, fit_start, fit_end, 
position_guess, position_limit_lower, position_limit_upper, position_hold, 
gamma_guess, gamma_limit_lower, gamma_limit_upper, gamma_hold, sigma_guess, 
sigma_limit_lower, sigma_limit_upper, sigma_hold, norm_guess, norm_limit_lower, 
norm_limit_upper, and norm_hold.


## 2. (Optional) Estimate background of spectrum
You can estimate backgrounds with `.fit_background()` by specifying estimaiton 
function via `func` argument, and a `kwargs` argument is additional arguments to 
the background estimating function, for example: 
```python
test_peak.fit_background(
    func=xps.linear_and_shirley,
    kwargs={
        "range_linear"  : (286, 297),
        "range_shirley" : (278, 290),
    }
)
```

The function passed for `func` argument must must have `xy` argument and return 
`pandas.DataFrame` at least including a column named `y_bg`.


## 3. Fit with parameters
Conduct `.fit()` method to fit and results are stored in `test_peak` object 
when the fitting succeeds.
```python
# Compute fitting 
test_peak.fit()

# Print fitting results
test_peak.print_resultparam()
```


## 4. Plot with accessors
After fitting, we can access plotting data with `.x`, `.y_raw` and `.y_fit` accesser 
as `pandas.Series`:
```python
import matplotlib as plt

# Plotting #
fig, ax = plt.subplots()
ax.plot(test_peak.x, test_peak.y_raw)
ax.plot(test_peak.x, test_peak.y_fit)
plt.show()
```

If some peaks are fitted at the same time, we can access each elemental peak by using 
`.y_eles` accessor:
```python
# Plot all elements of peaks
for col_name in test_peak.y_eles:
    ax.plot(test_peak.x, test_peak.y_eles[col_name])
```
`.y_eles` returns `pandas.DataFrame` which consists of y-axis data of each peak in 
columns.


## 5. Save the results and load it
To save fitting data, use `to_csv` method of `pandas.DataFrame`:
```python
# Saving fit results #
test_peak.xy_all.to_csv("xy.csv", index=False)
test_peak.resultparam.to_csv("resultparam.csv", index=False)
```

If data were saved as csv file, `Spectrum` class can load the fitted data:
```python
test_peak = pyspecfit.Spectrum.load_csv("xy.csv")
```

These component accessors are shortcuts for `.data`, for example `.x` is a shortened 
expression of `.data.x`.


# Dependencies
 - [Numpy](https://www.numpy.org/)
 - [pandas](https://pandas.pydata.org/)
 - [SciPy](https://scipy.org/)
 - [Matplotlib](https://matplotlib.org/)


# License
[MIT license](https://github.com/aacco/pyspecfit/blob/main/LICENSE)

