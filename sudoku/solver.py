"""Solve a standard 9x9 Sudoku using Z3 SMT constraints."""

from z3 import And, Distinct, Int, Solver, sat, unsat


def solve_sudoku(puzzle):
    """Return one solution, or None if unsatisfiable; 0 represents a blank."""
    if len(puzzle) != 9 or any(len(row) != 9 for row in puzzle):
        raise ValueError("The puzzle must have 9 rows and 9 columns.")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in puzzle for value in row):
        raise ValueError("Cells must be integers from 0 through 9.")

    cells = [[Int(f"cell_{r}_{c}") for c in range(9)] for r in range(9)]
    solver = Solver()

    # Each cell is an integer from 1 to 9.
    solver.add([And(1 <= cell, cell <= 9) for row in cells for cell in row])
    # Every row, column, and 3x3 box contains distinct values.
    solver.add([Distinct(row) for row in cells])
    solver.add([Distinct([cells[r][c] for r in range(9)]) for c in range(9)])
    solver.add([
        Distinct([cells[r + dr][c + dc] for dr in range(3) for dc in range(3)])
        for r in (0, 3, 6) for c in (0, 3, 6)
    ])
    # Preserve the given clues.
    solver.add([cells[r][c] == puzzle[r][c]
                for r in range(9) for c in range(9) if puzzle[r][c] != 0])

    result = solver.check()
    if result == unsat:
        return None
    if result != sat:
        raise RuntimeError(f"Z3 could not decide: {solver.reason_unknown()}")
    model = solver.model()
    return [[model.evaluate(cell).as_long() for cell in row] for row in cells]


if __name__ == "__main__":
    puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    solution = solve_sudoku(puzzle)
    print("No solution." if solution is None else
          "\n".join(" ".join(map(str, row)) for row in solution))
