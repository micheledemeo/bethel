"""Sample datasets shipped with bethel."""

from __future__ import annotations

from importlib import resources

import pandas as pd


def load_pop() -> pd.DataFrame:
    """Load the example population (1000 individuals).

    Columns
    -------
    strata :
        Sex × area factor levels
        (``F_area1`` … ``F_area4``, ``M_area1`` … ``M_area4``).
    income :
        Yearly income.
    books :
        Number of books read.
    sportDays :
        Total days of sporting activities.
    """
    data_path = resources.files("bethel").joinpath("data/pop.csv")
    with resources.as_file(data_path) as path:
        return pd.read_csv(path)
