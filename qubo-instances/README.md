# QS File Format

A `.qs` file stores one QUBO (quadratic unconstrained binary optimization) problem:
a sparse symmetric matrix `Q` plus a constant offset `c`. The objective is always
minimized over binary variables `x in {0,1}^n`.

## Layout

Plain text, whitespace separated:

| Part | Lines | Content |
| --- | --- | --- |
| Header | Any number, each starting with `#` | Comments. |
| Objective Offset | One header line `# ObjectiveOffset <c>` | Constant added to the energy. Present even when it is 0. |
| Size line | First non-comment line: `<n> <m>` | `n` variables, `m` entry lines follow. |
| Entries | `m` lines of `<i> <j> <q>` | 1-based indices with `i <= j` (upper triangle including the diagonal). |

The Objective Offset line is a comment by syntax, so read it before discarding `#` lines.
Only nonzero entries are listed, each pair `(i, j)` at most once.

## Semantics

```
E(x) = c + x^T Q x = c + sum_i Q[i,i] * x_i + 2 * sum_{i<j} Q[i,j] * x_i * x_j
```

- **Diagonal** `i i q`: linear term, contributes `q * x_i` once (since `x_i^2 = x_i`).
- **Off-diagonal** `i j q`: stored once but stands for both `Q[i,j]` and `Q[j,i]`, so it is
  counted twice and contributes `2 * q * x_i * x_j`. Adding it only once gives wrong energies.
- **Offset** `c`: does not change the minimizer; add it to the final objective value.

## Example

```
# ObjectiveOffset 5
3 4
1 1 -1
1 2 1
2 2 -1
3 3 -2
```

| x | E(x) |
| --- | --- |
| (0, 0, 0) | 5 |
| (1, 0, 0) | 4 |
| (1, 1, 0) | -1 - 1 + 2*1 + 5 = 5 |
| (1, 0, 1) | -1 - 2 + 5 = 2 |
| (1, 1, 1) | -1 - 1 - 2 + 2*1 + 5 = 3 |

Minimum: `E = 2` at `x = (1, 0, 1)`.

Note: `solve_qubo.py` currently adds each off-diagonal entry once, missing the factor 2.
