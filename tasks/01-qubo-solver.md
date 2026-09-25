# OpenCode Task: Implement a Gurobi QUBO Solver

## Goal

Implement a command-line QUBO solver in Python using `gurobipy`.

The program must:

1. read a QUBO instance from a text file;
2. construct an unconstrained binary quadratic Gurobi model;
3. solve it;
4. print the bit-string solution, objective value, and Gurobi runtime;
5. compute and print the XOR checksum of the solution bytes.

Use the project environment through `uv`.

## Input format

Example:

```text
# ObjectiveOffset 1
3 4
1 1 30024.0
1 2 -10008.0
1 3 -10008.0
2 3 5004.0
```

Blank lines may occur and should be ignored.

### Comments

Lines beginning with `#` are comments.

One special optional comment is recognized:

```text
# ObjectiveOffset VALUE
```

Parse `VALUE` as a floating-point number and add it exactly once to the final reported objective value.

If no `ObjectiveOffset` is present, use `0.0`.

Reject multiple conflicting `ObjectiveOffset` declarations.

### Header

The first non-comment, non-empty line contains:

```text
n nnz
```

where:

- `n` is the dimension of the square QUBO matrix;
- `nnz` is the number of explicitly stored nonzero entries that follow.

Validate `n > 0`, `nnz >= 0`, and that exactly `nnz` entry lines are present.

### Matrix entries

Each matrix entry has the form:

```text
i j value
```

Indices are 1-based in the file.

Validate:

```text
1 <= i <= n
1 <= j <= n
```

Reject duplicate `(i, j)` entries.

## Upper/lower triangular input

The input contains a single triangle of a symmetric QUBO matrix.

Accept both:

- upper triangular: all off-diagonal entries satisfy `i < j`;
- lower triangular: all off-diagonal entries satisfy `i > j`.

Diagonal entries are valid in either representation.

If off-diagonal entries occur on both sides of the diagonal, reject the input as malformed.

A diagonal-only matrix is valid.

## QUBO coefficient convention

Interpret the file as entries of the symmetric matrix `Q` in:

```text
x^T Q x
```

Therefore:

- a diagonal entry `Q[i,i]` contributes `Q[i,i] * x[i]`;
- an off-diagonal stored entry `Q[i,j]` contributes
  `2 * Q[i,j] * x[i] * x[j]`.

The factor of two is important because the symmetric matrix contains both
`Q[i,j]` and `Q[j,i]`.

For the example input, the quadratic polynomial before the offset is:

```text
30024*x1
- 20016*x1*x2
- 20016*x1*x3
+ 10008*x2*x3
```

## Gurobi model

Create exactly one binary variable per QUBO variable.

For example:

```python
x = model.addVars(n, vtype=GRB.BINARY, name="x")
```

There are no model constraints.

Build a Gurobi quadratic expression and set:

```python
model.setObjective(objective, GRB.MINIMIZE)
```

Do not linearize the quadratic objective and do not add auxiliary variables.

Prefer putting the objective offset directly into the Gurobi objective so
`model.ObjVal` already includes it.

Call:

```python
model.optimize()
```

Check the solver status before reading solution values.

## Command line

Implement a CLI such as:

```bash
uv run python qubo_solver.py INSTANCE_FILE
```

Use `argparse` or equivalent standard-library functionality.

Malformed input or solver failure must result in a nonzero exit code.

## Solution bit string

Print one bit for every variable in ascending variable order:

```text
x1 x2 ... xn
```

but without separators.

Example:

```text
0010011100011110011
```

Use a threshold such as:

```python
bit = 1 if value > 0.5 else 0
```

The output must contain exactly `n` binary digits.

## XOR checksum

Split the solution string from the left into 8-bit groups.

Example:

```text
0010011100011110011
```

becomes:

```text
00100111
00011110
011
```

Pad the final incomplete group with zeros **on the right**:

```text
00100111
00011110
01100000
```

Convert each group to an unsigned byte and XOR all bytes.

Print the result as two-digit uppercase hexadecimal:

```text
0x00
0x05
0xA7
0xFF
```

A helper such as this is encouraged:

```python
def xor_checksum(bit_string: str) -> int:
    ...
```

## Runtime

Report Gurobi's solver runtime:

```python
model.Runtime
```

Do not report file-parsing or Python startup time as solver time.

## Required output

Print at least:

```text
Solution: <bit-string>
Objective: <objective-value>
Runtime: <seconds> s
XOR: <two-digit-hex-byte>
```

Keep the format deterministic and simple.

## Recommended implementation structure

Separate parsing, model construction, solving, and checksum logic.

For example:

```python
def read_qubo(path):
    ...

def build_model(instance):
    ...

def solution_bit_string(variables, n):
    ...

def xor_checksum(bit_string):
    ...

def solve(instance):
    ...
```

A small dataclass for the parsed instance is encouraged.

## Required validation

At minimum detect:

- missing header;
- malformed `ObjectiveOffset`;
- invalid dimension;
- negative `nnz`;
- incorrect number of matrix entries;
- malformed entry lines;
- out-of-range indices;
- duplicate entries;
- mixed upper/lower triangular entries;
- nonnumeric values.

Do not silently accept malformed data if it changes the mathematical model.

## Tests

Add automated tests covering at least:

### Parser

- upper-triangular input;
- lower-triangular input;
- diagonal-only input;
- offset present and absent;
- blank lines/comments;
- wrong `nnz`;
- mixed triangles;
- out-of-range indices;
- duplicate entries.

### Objective construction

Verify that upper- and lower-triangular representations of the same matrix
produce the same objective and solution.

Explicitly test the off-diagonal factor of two.

For example:

```text
2 1
1 2 -1
```

represents:

```text
-2*x1*x2
```

### XOR checksum

Test bit-string lengths around byte boundaries, including:

```text
1, 7, 8, 9, 15, 16, 17
```

For example, the one-bit string:

```text
1
```

is padded to:

```text
10000000
```

and therefore yields:

```text
0x80
```

### End-to-end

Create at least one tiny instance whose optimum can be independently verified,
solve it, and check:

- bit string;
- objective including offset;
- XOR checksum.

For tiny test cases, a brute-force enumerator is encouraged as an independent
test oracle. The production solver must still use Gurobi.

## Code quality

Before finishing, run:

```bash
./scripts/check.sh
```

Do not suppress legitimate Ruff, Pyright, pytest, or solver failures.

## Gurobi safety

Do not:

- modify or copy the participant's Gurobi license;
- print license credentials;
- commit license credentials;
- add a different solver;
- add unnecessary constraints;
- linearize the QUBO.

## Definition of done

The task is complete only when:

1. both upper- and lower-triangular input are supported;
2. the symmetric-Q interpretation and off-diagonal factor of two are correct;
3. `ObjectiveOffset` is included exactly once;
4. Gurobi receives binary variables and a quadratic objective with no constraints;
5. the problem is minimized;
6. solver status is checked;
7. the solution string contains exactly `n` bits in variable order;
8. the XOR checksum, including right-padding, is correct;
9. objective and Gurobi runtime are printed;
10. malformed inputs generate useful failures;
11. automated tests cover parsing, optimization, and checksum behavior;
12. `./scripts/check.sh` passes;
13. `git status` and `git diff` show only intentional changes.

Before finishing, summarize:

- files changed;
- implementation approach;
- verification commands run;
- test result.
