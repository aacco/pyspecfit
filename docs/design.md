# Design

This document describes the design philosophy and architecture of **pyspecfit**.

The package is designed around a simple idea:

> **A spectrum analysis should be represented as a single object while numerical data remain independent from analysis logic.**

This separation improves readability, reproducibility, and extensibility.

---

# Architecture

The library consists of two core classes.

```text
                Spectrum
                    │
                    │ owns
                    ▼
                xySeries
                    │
                    ▼
        MultiIndex pandas.DataFrame
```

The responsibilities are intentionally separated.

| Class | Responsibility |
|--------|----------------|
| `Spectrum` | Analysis workflow and state management |
| `xySeries` | Storage of numerical spectral data |

---

# Design Principles

The architecture follows three principles.

## Separation of Data and Workflow

Although `pyspecfit` is not explicitly designed around a software architecture pattern, its core classes naturally separate numerical data from analysis workflow.

- `Spectrum` manages the analysis session, including fitting parameters, optimization, and result management.
- `xySeries` is responsible for storing spectral data and processed results.

This separation reduces coupling between data representation and analysis logic, making the codebase easier to maintain and extend. For example, new peak models or fitting algorithms can be introduced without changing how spectral data are organized, while additional data representations or export formats can be implemented without modifying the fitting workflow.

---

## 1. Separation of Concerns

The package separates

- numerical data
- analysis workflow
- background estimation

into independent components.

```text
Spectrum
    │
    ├── fitting workflow
    ├── optimization
    ├── result management
    │
    ▼
xySeries
    │
    ├── x
    ├── raw spectrum
    ├── background
    ├── fitted spectrum
    └── peak components
```

This keeps each class focused on a single responsibility.

---

## 2. Stateful Analysis

A `Spectrum` object represents an **analysis session**, not merely a fitting function.

Instead of returning multiple arrays,

```python
result = fit(...)
```

the analysis state is stored inside the object.

```python
sp.fit()
```

updates

- optimized parameters
- fitted spectrum
- peak components
- fitting statistics

without requiring users to manually synchronize intermediate data.

This workflow resembles machine learning libraries such as scikit-learn, where a model object stores both configuration and fitted results.

---

## 3. Reproducibility

All information required to reproduce an analysis is contained in

- raw spectrum
- fitting parameter table
- registered backgrounds
- fitted results

These are managed by a single `Spectrum` instance.

The fitting conditions themselves are stored in CSV files rather than embedded in Python code, allowing analyses to be reproduced without modifying scripts.

---

# Spectrum

`Spectrum` is the central object of the package.

Conceptually,

```text
Raw spectrum
      │
      ▼
Spectrum
      │
      ├── register background
      ├── optimize peaks
      ├── calculate peak components
      ├── calculate fitting statistics
      ▼
Results
```

Internally, `Spectrum` owns

- `xySeries`
- fitting parameters
- optimization results
- processed fitting parameters

and coordinates the entire workflow.

Its primary role is **workflow orchestration**, not numerical computation.

---

## Responsibilities

`Spectrum` is responsible for

- constructing an analysis session,
- managing fitting parameters,
- registering backgrounds,
- executing peak fitting,
- updating fitting results,
- exporting processed information.

It intentionally delegates numerical data storage to `xySeries`.

---

# xySeries

`xySeries` stores all numerical spectral data.

Rather than managing independent arrays,

```python
x
y_raw
y_bg
y_fit
peak1
peak2
...
```

all information is organized into a single MultiIndex `pandas.DataFrame`.

Conceptually,

```text
base
 ├── x
 ├── y_raw
 ├── y_bg
 └── y_fit

bg
 ├── pybaselines
 └── custom

peak
 ├── Peak A
 ├── Peak B
 └── Peak C
```

This provides a unified representation of the complete analysis.

---

## Why a MultiIndex DataFrame?

Using a single MultiIndex DataFrame provides several advantages.

### Unified storage

All numerical results remain synchronized.

### Easy export

The complete analysis can be exported using

```python
sp.data.xy_all.to_csv(...)
```

without collecting individual arrays.

### Flexible visualization

Backgrounds and peak components can be accessed directly for plotting.

### Extensibility

Additional background algorithms or peak components can be added without changing the data structure.

---

# Background Registration

Background estimation is intentionally separated from the fitting engine.

Instead of implementing specific baseline algorithms,

`pyspecfit` accepts externally generated backgrounds.

```text
Raw spectrum
      │
      ▼
Background algorithm
      │
      ▼
register_new_bg()
      │
      ▼
Peak fitting
```

This allows users to combine `pyspecfit` with

- pybaselines
- custom baseline estimators
- laboratory-specific workflows

without modifying the optimization code.

The fitting engine therefore remains independent of any particular baseline estimation strategy.

---

# Data Flow

A typical analysis proceeds as follows.

```text
CSV
 │
 ▼
Spectrum
 │
 ▼
xySeries

      │
      ├── Raw spectrum
      ├── Background
      └── Fitting parameters

      │
      ▼

Optimization

      │
      ▼

Updated xySeries

      │
      ├── y_fit
      ├── peak components
      └── processed parameters
```

Every step updates the analysis session rather than creating disconnected intermediate objects.

---

# Extensibility

The architecture is intended to be extended in three directions.

## Peak Models

Additional peak models can be implemented independently of `xySeries`.

Examples include

- Gaussian
- Lorentzian
- Doniach–Šunjić
- Pseudo-Voigt

---

## Background Algorithms

Background estimation is external by design.

New algorithms require no modification to the fitting engine.

---

## Input/Output

Because all processed spectra are stored in `xySeries`, additional export formats (HDF5, NetCDF, Excel, etc.) can be implemented without modifying `Spectrum`.

---

# Summary

The architecture of **pyspecfit** is based on a clear separation between **analysis workflow** and **numerical data**.

- `Spectrum` manages the analysis session.
- `xySeries` stores the spectral data.
- Background estimation remains independent from peak fitting.

This design provides a workflow that is modular, reproducible, and straightforward to extend for future spectroscopic analysis methods.