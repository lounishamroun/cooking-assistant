"""Cooking Assistant package.

Exposes utilities for:
* Data acquisition & loading (``data``)
* Seasonal labeling & review volume analysis (``analysis``)
* Bayesian ranking computation (``analysis.scoring``)
* Results persistence (``utils.results``)
* Multi-signal classifier output consumption (via classified recipes file)

Public API re-exports in submodules are limited to the core analytical and
I/O functions to keep the surface stable for documentation and importers.
"""

__version__ = "0.1.0"
__author__ = "Lounis Hamroun, Alexandre Donnat, Omar Fekih, Leo Ivars"
