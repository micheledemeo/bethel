"""Bethel's algorithm for multivariate stratified sample allocation.

Python port of the CRAN R package `bethel`
(https://cran.r-project.org/package=bethel), authored by Michele De Meo.
"""

from bethel.bth import (
    ADJUSTED_SAMPLE_COL,
    BETHEL_SAMPLE_COL,
    COST_COL,
    CV_COL,
    MIN_RATE_COL,
    MIN_SAMPLE_COL,
    POPULATION_SIZE_COL,
    STRATUM_COL,
    TOTAL_COL,
    bth,
    prepare_strata,
    prepare_targets,
)
from bethel.datasets import load_pop

__all__ = [
    "ADJUSTED_SAMPLE_COL",
    "BETHEL_SAMPLE_COL",
    "COST_COL",
    "CV_COL",
    "MIN_RATE_COL",
    "MIN_SAMPLE_COL",
    "POPULATION_SIZE_COL",
    "STRATUM_COL",
    "TOTAL_COL",
    "bth",
    "prepare_strata",
    "prepare_targets",
    "load_pop",
]
__version__ = "0.2.1"
