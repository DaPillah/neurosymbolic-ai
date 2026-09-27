"""Bottom-up enumerative synthesis for a tiny integer arithmetic language."""

import argparse
import operator
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple


Example = Tuple[int, int, int]
OPERATIONS = {"+": operator.add, "-": operator.sub, "*": operator.mul}
TERMINALS = ("x", "y", "0", "1", "2")


@dataclass(frozen=True)
class Candidate:
    program: str
    outputs: Tuple[int, ...]


def parse_examples(text: str) -> list[Example]:
    """Read comma-separated x, y, output rows; allow blank lines and # comments."""
    examples = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split(",")
        if len(fields) != 3:
            raise ValueError(f"line {line_number}: expected three comma-separated integers")
        try:
            x, y, output = map(int, fields)
        except ValueError as exc:
            raise ValueError(f"line {line_number}: expected integers") from exc
        examples.append((x, y, output))
    if not examples:
        raise ValueError("provide at least one input-output example")
    return examples


def evaluate(program: str, x: int, y: int) -> int:
    """Evaluate and validate a prefix program using a stack, right to left."""
    stack = []
    terminals = {"x": x, "y": y, "0": 0, "1": 1, "2": 2}
    for token in reversed(program.split()):
        if token in terminals:
            stack.append(terminals[token])
        elif token in OPERATIONS:
            if len(stack) < 2:
                raise ValueError(f"operator {token!r} is missing an operand")
            left, right = stack.pop(), stack.pop()
            stack.append(OPERATIONS[token](left, right))
        else:
            raise ValueError(f"invalid token: {token!r}")
    if len(stack) != 1:
        raise ValueError("expected exactly one complete expression")
    return stack[0]


def synthesize(
    examples: Iterable[Example], max_size: int = 9, *, prune: bool = True
) -> Optional[str]:
    """Return a minimum-token matching program, or None within the size bound.

    Ties are deterministic: terminals x,y,0,1,2; then operators +,-,*;
    then increasing left-child size; then each child's generation order.
    Pruning retains the first (therefore smallest) representative of each
    output vector. Set prune=False to enumerate every syntactic expression.
    """
    if type(max_size) is not int or max_size < 1:
        raise ValueError("max_size must be a positive integer")
    examples = list(examples)
    if not examples:
        raise ValueError("provide at least one input-output example")
    known_outputs = {}
    for example in examples:
        if len(example) != 3 or any(type(value) is not int for value in example):
            raise ValueError("each example must contain exactly three integers")
        x, y, output = example
        if (x, y) in known_outputs and known_outputs[x, y] != output:
            raise ValueError(f"conflicting outputs for inputs ({x}, {y})")
        known_outputs[x, y] = output

    target = tuple(output for _, _, output in examples)
    # by_size[n] contains expressions with exactly n tokens.
    by_size: dict[int, list[Candidate]] = {1: []}
    seen: set[Tuple[int, ...]] = set()
    for token in TERMINALS:
        outputs = tuple(
            x if token == "x" else y if token == "y" else int(token)
            for x, y, _ in examples
        )
        if outputs == target:
            return token
        if not prune or outputs not in seen:
            by_size[1].append(Candidate(token, outputs))
            seen.add(outputs)

    # Every binary node adds one operator and two odd-sized subexpressions,
    # so valid programs have only odd sizes: 1, 3, 5, ...
    for size in range(3, max_size + 1, 2):
        by_size[size] = []
        for symbol, operation in OPERATIONS.items():
            for left_size in range(1, size - 1, 2):
                right_size = size - 1 - left_size
                for left in by_size[left_size]:
                    for right in by_size[right_size]:
                        outputs = tuple(
                            operation(a, b) for a, b in zip(left.outputs, right.outputs)
                        )
                        if outputs == target:
                            return f"{symbol} {left.program} {right.program}"
                        if prune and outputs in seen:
                            continue
                        program = f"{symbol} {left.program} {right.program}"
                        by_size[size].append(Candidate(program, outputs))
                        seen.add(outputs)
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("examples", help="CSV file of x,y,output rows, or - for stdin")
    parser.add_argument("--max-size", type=int, default=9, help="token limit (default: 9)")
    parser.add_argument(
        "--no-pruning", action="store_true", help="enumerate all expressions; much slower"
    )
    args = parser.parse_args(argv)
    try:
        text = sys.stdin.read() if args.examples == "-" else Path(args.examples).read_text()
        program = synthesize(
            parse_examples(text), args.max_size, prune=not args.no_pruning
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if program is None:
        print(f"No solution found with at most {args.max_size} tokens.", file=sys.stderr)
        return 1
    print(program)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
