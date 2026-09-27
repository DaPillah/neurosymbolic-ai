import contextlib
import io
import itertools
import unittest
from pathlib import Path

from synthesizer import evaluate, main, parse_examples, synthesize


class SynthesisTests(unittest.TestCase):
    def test_assignment_example(self):
        examples = [(1, 2, 3), (4, 5, 9), (0, 7, 7)]
        for prune in (False, True):
            self.assertEqual(synthesize(examples, prune=prune), "+ x y")

    def test_all_terminals(self):
        for token in ("x", "y", "0", "1", "2"):
            examples = [(x, y, evaluate(token, x, y)) for x, y in [(3, 7), (-2, 4)]]
            self.assertEqual(synthesize(examples), token)

    def test_arithmetic_and_nested_expression(self):
        points = list(itertools.product(range(-2, 3), repeat=2))
        for expected in ("- x y", "- y x", "* x y", "- * x x y", "* + x 1 - y 2"):
            examples = [(x, y, evaluate(expected, x, y)) for x, y in points]
            program = synthesize(examples, max_size=len(expected.split()))
            self.assertIsNotNone(program)
            for x, y, output in examples:
                self.assertEqual(evaluate(program, x, y), output)

    def test_minimum_size_and_bound(self):
        examples = [(x, y, x * x - y) for x, y in itertools.product(range(-2, 3), repeat=2)]
        self.assertIsNone(synthesize(examples, max_size=4))
        self.assertEqual(synthesize(examples, max_size=5), "- * x x y")

    def test_first_match_is_returned(self):
        self.assertEqual(synthesize([(1, 1, 1)]), "x")

    def test_duplicates_and_generator_input(self):
        self.assertEqual(synthesize(iter([(3, 4, 7), (3, 4, 7)])), "+ x y")

    def test_pruning_matches_independent_exhaustive_reference(self):
        # Independently enumerate all size-1 and size-3 programs and their
        # output vectors, then require the same first answer in both modes.
        terminals = ["x", "y", "0", "1", "2"]
        programs = terminals + [
            f"{op} {a} {b}" for op in ("+", "-", "*") for a in terminals for b in terminals
        ]
        points = [(-2, 3), (0, -1), (4, 2)]
        first_by_outputs = {}
        for program in programs:
            outputs = tuple(evaluate(program, x, y) for x, y in points)
            first_by_outputs.setdefault(outputs, program)
        for outputs, expected in first_by_outputs.items():
            examples = [(x, y, out) for (x, y), out in zip(points, outputs)]
            for prune in (False, True):
                self.assertEqual(synthesize(examples, max_size=3, prune=prune), expected)

    def test_invalid_examples(self):
        for examples in ([], [(1, 2)], [(1, 2, 3.0)], [(1, 2, 3), (1, 2, 4)]):
            with self.assertRaises(ValueError):
                synthesize(examples)

    def test_invalid_bound(self):
        for bound in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                synthesize([(0, 0, 0)], max_size=bound)


class EvaluationTests(unittest.TestCase):
    def test_operand_order_and_nesting(self):
        self.assertEqual(evaluate("- * x x y", -3, 2), 7)
        self.assertEqual(evaluate("- y x", -3, 2), 5)

    def test_large_integers(self):
        self.assertEqual(evaluate("* x x", 10**50, 0), 10**100)

    def test_invalid_programs(self):
        for program in ("", "+ x", "x y", "/ x y", "3", "-1", "+ x y y"):
            with self.assertRaises(ValueError):
                evaluate(program, 1, 2)


class InputAndCliTests(unittest.TestCase):
    def test_comments_whitespace_and_negatives(self):
        self.assertEqual(parse_examples("# heading\n\n -1, 2, 1 # row\n"), [(-1, 2, 1)])

    def test_bad_input(self):
        for text in ("", "# comment", "1,2", "1,2,3,4", "x,y,z", "1,2,3.5"):
            with self.assertRaises(ValueError):
                parse_examples(text)

    def test_cli_success(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "addition.csv"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main([str(path)])
        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue(), "+ x y\n")

    def test_cli_no_solution_within_bound(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "addition.csv"
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            status = main([str(path), "--max-size", "1"])
        self.assertEqual(status, 1)
        self.assertIn("at most 1 tokens", output.getvalue())

    def test_cli_missing_file(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            status = main([str(Path(__file__).parent / "nonexistent.csv")])
        self.assertEqual(status, 2)
        self.assertIn("Error:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
