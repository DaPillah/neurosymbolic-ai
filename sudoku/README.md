# Sudoku with SMT

A 9x9 Sudoku solver using Python and [Z3](https://pypi.org/project/z3-solver/).
Use `0` for blank cells. `solve_sudoku(puzzle)` returns one solved grid, or
`None` when the clues are inconsistent. Invalid inputs raise `ValueError`.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python solver.py
python -m unittest -v
```

The core logic declares 81 integer variables, constrains their values to 1–9,
requires distinct values in each row, column, and 3x3 box, and fixes the supplied
clues. Z3 performs the search. Python comprehensions construct constraints and
extract the model; they do not implement a procedural solving loop.

AI assistance was used to write and verify this implementation.
