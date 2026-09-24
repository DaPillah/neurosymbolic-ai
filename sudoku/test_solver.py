import unittest

from solver import solve_sudoku


class SudokuTests(unittest.TestCase):
    def test_known_puzzle(self):
        puzzle = [list(map(int, row)) for row in (
            "530070000", "600195000", "098000060",
            "800060003", "400803001", "700020006",
            "060000280", "000419005", "000080079",
        )]
        expected = [list(map(int, row)) for row in (
            "534678912", "672195348", "198342567",
            "859761423", "426853791", "713924856",
            "961537284", "287419635", "345286179",
        )]
        self.assertEqual(solve_sudoku(puzzle), expected)
        self.assertEqual(solve_sudoku(expected), expected)

    def test_conflicting_clues(self):
        # Test row, column, and box conflicts separately.
        for other in ((0, 4), (4, 0), (1, 1)):
            with self.subTest(other=other):
                puzzle = [[0] * 9 for _ in range(9)]
                puzzle[0][0] = 5
                puzzle[other[0]][other[1]] = 5
                self.assertIsNone(solve_sudoku(puzzle))

    def test_invalid_inputs(self):
        for puzzle in ([], [[0] * 8 for _ in range(9)]):
            with self.assertRaises(ValueError):
                solve_sudoku(puzzle)
        for value in (-1, 10, 1.5, "5", True):
            puzzle = [[0] * 9 for _ in range(9)]
            puzzle[0][0] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                solve_sudoku(puzzle)


if __name__ == "__main__":
    unittest.main()
