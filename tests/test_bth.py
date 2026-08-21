import pandas as pd
import pytest

from bethel import bth, load_pop, prepare_strata, prepare_targets


def test_load_pop_shape():
    pop = load_pop()
    assert pop.shape == (1000, 4)
    assert list(pop.columns) == ["strata", "income", "books", "sportDays"]
    assert pop["strata"].nunique() == 8


def test_bth_uniform_cv():
    pop = load_pop()
    var_cols = ["income", "books", "sportDays"]
    strata = prepare_strata(pop, "strata", var_cols)
    targets = prepare_targets(pop, var_cols, cv=0.05)
    result = bth(strata, targets)

    assert list(result.columns) == ["strata", "bethel_sample", "adjusted_sample"]
    assert len(result) == 8
    assert (result["bethel_sample"] >= 1).all()
    assert (result["adjusted_sample"] >= result["bethel_sample"]).all()
    assert (result["adjusted_sample"] <= strata["population_size"].to_numpy()).all()
    assert (result["adjusted_sample"] >= 3).all()


def test_bth_heterogeneous_cv_changes_allocation():
    pop = load_pop()
    var_cols = ["income", "books", "sportDays"]
    strata = prepare_strata(pop, "strata", var_cols)
    uniform = bth(strata, prepare_targets(pop, var_cols, cv=0.05))
    heterogeneous = bth(strata, prepare_targets(pop, var_cols, cv=[0.05, 0.01, 0.2]))
    assert heterogeneous["bethel_sample"].sum() > uniform["bethel_sample"].sum()


def test_single_variable():
    """One variance column uses the univariate allocation path."""
    strata = pd.DataFrame(
        {
            "strata": ["A", "B"],
            "var_y": [10.0, 20.0],
            "population_size": [100, 200],
            "cost": [1.0, 1.0],
            "min_sample": [3, 3],
            "min_rate": [0.04, 0.04],
        }
    )
    targets = pd.DataFrame({"cv": [0.05], "total": [1000.0]})
    result = bth(strata, targets)
    assert len(result) == 2
    assert (result["bethel_sample"] > 0).all()


def test_validation_errors():
    strata = pd.DataFrame({"strata": ["A"], "population_size": [10]})
    targets = pd.DataFrame({"cv": [0.05], "total": [1.0]})
    with pytest.raises(ValueError, match="missing required columns"):
        bth(strata, targets)

    strata = pd.DataFrame(
        {
            "strata": ["A"],
            "var_y": [1.0],
            "population_size": [10],
            "cost": [1.0],
            "min_sample": [3],
            "min_rate": [0.04],
        }
    )
    targets = pd.DataFrame({"cv": [0.05, 0.05], "total": [1.0, 2.0]})
    with pytest.raises(ValueError, match="number of variance columns"):
        bth(strata, targets)


def test_matches_cran_r_package_reference():
    """Golden values from CRAN bethel 0.2 run under R 4.3.3."""
    pop = load_pop()
    var_cols = ["income", "books", "sportDays"]
    strata = prepare_strata(pop, "strata", var_cols)
    result = bth(strata, prepare_targets(pop, var_cols, cv=0.05))
    assert result["bethel_sample"].tolist() == [25, 21, 19, 7, 21, 29, 30, 10]
    assert result["adjusted_sample"].tolist() == [25, 21, 19, 7, 21, 29, 30, 10]

    result_alt = bth(strata, prepare_targets(pop, var_cols, cv=[0.05, 0.01, 0.2]))
    assert result_alt["bethel_sample"].tolist() == [120, 85, 105, 37, 96, 137, 149, 45]
