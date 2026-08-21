"""Bethel's algorithm for multivariate stratified sample allocation."""

from __future__ import annotations

import numpy as np
import pandas as pd

STRATUM_COL = "strata"
POPULATION_SIZE_COL = "population_size"
COST_COL = "cost"
MIN_SAMPLE_COL = "min_sample"
MIN_RATE_COL = "min_rate"
CV_COL = "cv"
TOTAL_COL = "total"
BETHEL_SAMPLE_COL = "bethel_sample"
ADJUSTED_SAMPLE_COL = "adjusted_sample"

STRATA_META_COLS = (
    POPULATION_SIZE_COL,
    COST_COL,
    MIN_SAMPLE_COL,
    MIN_RATE_COL,
)
TARGET_COLS = (CV_COL, TOTAL_COL)


def _variance_columns(strata: pd.DataFrame) -> list[str]:
    return [
        column
        for column in strata.columns
        if column not in (STRATUM_COL, *STRATA_META_COLS)
    ]


def bth(
    strata: pd.DataFrame | np.ndarray,
    targets: pd.DataFrame | np.ndarray,
    eps: float = 1e-10,
) -> pd.DataFrame:
    """Compute sample sizes with Bethel's procedure (1989).

    Determines total sample size and allocation across strata so as to
    minimize costs under CV precision constraints in the multivariate case.

    Parameters
    ----------
    strata :
        Stratum-level inputs. Required columns:

        - ``strata``: stratum label
        - one or more variance columns (e.g. ``var_income``)
        - ``population_size``: population size ``N`` in each stratum
        - ``cost``: unit cost per interview (often 1 for all strata)
        - ``min_sample``: absolute minimum sample size (e.g. 3)
        - ``min_rate``: minimum sampling rate (e.g. 0.04)

    targets :
        Variable-level precision constraints. Required columns:

        - ``cv``: target coefficient of variation
        - ``total``: estimated population total

        Must contain one row per variance column in ``strata``.

    eps :
        Convergence tolerance for the iterative algorithm (default ``1e-10``).

    Returns
    -------
    pandas.DataFrame
        Columns:

        - ``strata``: stratum label
        - ``bethel_sample``: Bethel sample size (ceiling of the continuous solution)
        - ``adjusted_sample``: sample size after minimum constraints and cap at ``N``

    References
    ----------
    Bethel, J.W. (1989). Sample Allocation in Multivariate Surveys.
    *Survey Methodology*, Vol. 15, pp. 47-57.

    Chromy, J.B. (1987). Design Optimization With Multiple Objectives.
    *Proceedings of the Section on Survey Research Methods*, ASA, pp. 194-199.
    """
    strata = pd.DataFrame(strata).copy()
    targets = pd.DataFrame(targets).copy()

    missing_strata = [
        column for column in (STRATUM_COL, *STRATA_META_COLS) if column not in strata.columns
    ]
    if missing_strata:
        raise ValueError(f"strata is missing required columns: {missing_strata}")

    missing_targets = [column for column in TARGET_COLS if column not in targets.columns]
    if missing_targets:
        raise ValueError(f"targets is missing required columns: {missing_targets}")

    variance_cols = _variance_columns(strata)
    if not variance_cols:
        raise ValueError("strata must include at least one variance column.")
    if len(variance_cols) != len(targets):
        raise ValueError(
            "the number of variance columns in strata must equal the number of rows in targets."
        )

    variances = strata[variance_cols].to_numpy(dtype=float)
    population_size = strata[POPULATION_SIZE_COL].to_numpy(dtype=float)
    costs = strata[COST_COL].to_numpy(dtype=float).reshape(-1, 1)
    min_sample = strata[MIN_SAMPLE_COL].to_numpy(dtype=float)
    min_rate = strata[MIN_RATE_COL].to_numpy(dtype=float)
    cv = targets[CV_COL].to_numpy(dtype=float)
    totals = targets[TOTAL_COL].to_numpy(dtype=float)

    if np.sum(variances) == 0:
        raise ValueError(
            "All strata have zero variance. "
            "The optimal sample size is one unit in each stratum."
        )
    if not np.all(population_size > 0):
        raise ValueError("population_size must be greater than zero in every stratum.")
    if not np.all(costs.ravel() > 0):
        raise ValueError("cost must be greater than zero in every stratum.")
    if not np.all(min_sample > 0):
        raise ValueError("min_sample must be greater than zero in every stratum.")
    if not np.all(min_rate > 0):
        raise ValueError("min_rate must be greater than zero in every stratum.")

    # numerator: variables x strata = variance_hj * N_h^2
    numerator = (variances * (population_size**2)[:, None]).T
    # denominator: variables = CV^2 * total^2 + sum_h variance_hj * N_h
    denominator = (cv**2) * (totals**2) + variances.T @ population_size

    if len(variance_cols) == 1:
        allocation_matrix = (numerator / denominator).reshape(-1, 1)
    else:
        allocation_matrix = (np.diag(1.0 / denominator) @ numerator).T

    variable_weights = np.full(
        (allocation_matrix.shape[1], 1),
        1.0 / allocation_matrix.shape[1],
        dtype=float,
    )
    not_converged = np.ones((allocation_matrix.shape[1], 1), dtype=bool)

    while np.sum(not_converged) > 0:
        previous_weights = variable_weights
        weighted_allocation = allocation_matrix @ variable_weights
        sqrt_allocation = np.sqrt(weighted_allocation)
        sqrt_costs = np.sqrt(costs)
        scaling = sqrt_allocation * (sqrt_costs.T @ sqrt_allocation).item()
        inverse_sample_sizes = sqrt_costs / scaling
        inverse_sample_sizes = np.where(np.isinf(inverse_sample_sizes), 1e9, inverse_sample_sizes)

        allocation_dot_inverse = allocation_matrix.T @ inverse_sample_sizes
        weight_update = previous_weights * (allocation_dot_inverse**2)
        variable_weights = weight_update / np.sum(weight_update).item()
        not_converged = np.abs(variable_weights - previous_weights) > eps

    bethel_sample = np.ceil(1.0 / inverse_sample_sizes.ravel())
    floored_sample = np.maximum(
        np.maximum(min_sample, np.ceil(min_rate * population_size)),
        bethel_sample,
    )
    adjusted_sample = np.minimum(floored_sample, population_size)

    return pd.DataFrame(
        {
            STRATUM_COL: strata[STRATUM_COL].to_numpy(),
            BETHEL_SAMPLE_COL: bethel_sample.astype(int),
            ADJUSTED_SAMPLE_COL: adjusted_sample.astype(int),
        }
    )


def prepare_strata(
    pop: pd.DataFrame,
    strata_col: str,
    var_cols: list[str],
    cost: float | list[float] | np.ndarray = 1.0,
    min_sample: float | list[float] | np.ndarray = 3.0,
    min_rate: float | list[float] | np.ndarray = 0.04,
) -> pd.DataFrame:
    """Build the ``strata`` input from a unit-level population frame.

    Mirrors the preparatory steps in the R package examples (``tapply`` +
    variances, population counts, cost and minimum sample constraints).
    """
    grouped = pop.groupby(strata_col, observed=True)
    parts = {
        f"var_{variable}": grouped[variable].var(ddof=1) for variable in var_cols
    }
    parts[POPULATION_SIZE_COL] = grouped[var_cols[0]].size()
    strata = pd.DataFrame(parts).reset_index().rename(columns={strata_col: STRATUM_COL})

    n_strata = len(strata)
    strata[COST_COL] = np.broadcast_to(np.asarray(cost, dtype=float), n_strata)
    strata[MIN_SAMPLE_COL] = np.broadcast_to(np.asarray(min_sample, dtype=float), n_strata)
    strata[MIN_RATE_COL] = np.broadcast_to(np.asarray(min_rate, dtype=float), n_strata)
    return strata


def prepare_targets(
    pop: pd.DataFrame,
    var_cols: list[str],
    cv: float | list[float] | np.ndarray = 0.05,
) -> pd.DataFrame:
    """Build the ``targets`` input (CV and estimated totals)."""
    totals = pop[var_cols].sum().to_numpy(dtype=float)
    cv_values = np.broadcast_to(np.asarray(cv, dtype=float), len(var_cols))
    return pd.DataFrame({CV_COL: cv_values, TOTAL_COL: totals})
