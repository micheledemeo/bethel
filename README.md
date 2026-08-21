# bethel

Python port of the CRAN R package
[bethel](https://cran.r-project.org/package=bethel): sample size and
allocation according to **Bethel's procedure** (1989) for multivariate
stratified surveys.

Minimizes survey costs under coefficient-of-variation (CV) constraints
on several target estimates.

## Install

From PyPI (after release):

```bash
pip install bethel
```

From source:

```bash
pip install -e .
```

## Examples

The worked example from the CRAN R package help page (`?bth`) is in
[`notebooks/bethel.ipynb`](notebooks/bethel.ipynb): dataset `pop`, variables
`income`, `books`, `sportDays`, same parameters and expected results as R.

```bash
pip install -e ".[notebook]"
jupyter notebook notebooks/bethel.ipynb
```

Minimal usage:

```python
from bethel import bth, load_pop, prepare_strata, prepare_targets

pop = load_pop()
var_cols = ["income", "books", "sportDays"]
strata = prepare_strata(pop, "strata", var_cols, cost=1, min_sample=3, min_rate=0.04)
targets = prepare_targets(pop, var_cols, cv=0.05)
bth(strata, targets)
```

## API

| Function | Role |
|---|---|
| `bth(strata, targets, eps=1e-10)` | Core Bethel allocation (same role as R `bth`) |
| `prepare_strata(...)` | Build `strata` from a unit-level population |
| `prepare_targets(...)` | Build `targets` (CV + totals) |
| `load_pop()` | Example population (1000 rows) |

### Input `strata`

| Column | Content |
|---|---|
| `strata` | Stratum label |
| `var_*` | Estimated variances of the target variables |
| `population_size` | Population size `N` |
| `cost` | Unit cost per interview |
| `min_sample` | Absolute minimum sample size |
| `min_rate` | Minimum sampling rate |

### Input `targets`

| Column | Content |
|---|---|
| `cv` | Target coefficient of variation |
| `total` | Estimated population total |

One row in `targets` is required for each variance column in `strata`.

### Output

- `bethel_sample` — continuous Bethel solution (ceiling)
- `adjusted_sample` — after minimum constraints and cap at `N`

## References

- Bethel, J.W. (1989). Sample Allocation in Multivariate Surveys.
  *Survey Methodology*, 15, 47–57.
- Chromy, J.B. (1987). Design Optimization With Multiple Objectives.
  *ASA Survey Research Methods*, 194–199.

## Author

Michele De Meo \<micheledemeo@gmail.com\>

## License

GPL (≥ 2), same as the R package.

---

*R-to-Python migration with a little help from LLMs. Bethel's algorithm (1989) is all his; the Python port had some AI assistance.*
