# OpenCode Task: Implement and Explore the Ackermann Function in Rust

## Goal

Implement the Ackermann function in Rust exactly according to the recurrence below, then experimentally determine how far the implementation can compute:

- `ack(3, m)`
- `ack(4, m)`

for increasing integer values of `m`.

The result should be a small Rust program plus tests and a short report of the largest `m` values successfully computed on the current machine.

The purpose of the exercise is not only to obtain values, but also to observe how quickly a mathematically simple recursive definition becomes computationally difficult.

---

## 1. Ackermann function

Implement the following function:

```text
function ack(n, m)
    if n = 0
        return m + 1
    else if m = 0
        return ack(n - 1, 1)
    else
        return ack(n - 1, ack(n, m - 1))
```

In mathematical notation:

```text
ack(0, m) = m + 1
ack(n, 0) = ack(n - 1, 1)              for n > 0
ack(n, m) = ack(n - 1, ack(n, m - 1))  for n > 0 and m > 0
```

Use nonnegative integer arguments only.

---

## 2. Rust implementation

Implement the function in Rust.

Start with a direct recursive implementation that mirrors the definition as closely as possible.

A suitable signature is:

```rust
fn ack(n: u32, m: u128) -> Option<u128>
```

or another integer representation that gives equivalent or better overflow handling.

### Requirements

The implementation must:

- preserve the semantics of the recurrence;
- use nonnegative integer inputs;
- detect arithmetic overflow rather than silently wrapping;
- not use `unsafe`;
- not silently return incorrect results after overflow;
- clearly distinguish:
  - a successfully computed value;
  - arithmetic overflow;
  - a run terminated because of a practical resource limit.

Using checked arithmetic such as `checked_add` is preferred.

Do not compile the benchmark with integer-overflow behavior that silently wraps values.

---

## 3. Correctness tests

Before exploring large values, add tests for small known values.

At minimum verify:

```text
ack(0, 0) = 1
ack(0, 5) = 6

ack(1, 0) = 2
ack(1, 1) = 3
ack(1, 5) = 7

ack(2, 0) = 3
ack(2, 1) = 5
ack(2, 2) = 7
ack(2, 3) = 9

ack(3, 0) = 5
ack(3, 1) = 13
ack(3, 2) = 29
ack(3, 3) = 61
ack(3, 4) = 125

ack(4, 0) = 13
```

Also test the implementation against these identities for small values:

```text
ack(1, m) = m + 2
ack(2, m) = 2m + 3
ack(3, m) = 2^(m + 3) - 3
```

Use the identities only as **test oracles**.

The primary implementation under test must still implement the Ackermann recurrence.

---

## 4. Command-line interface

Create a command-line program that can evaluate one invocation at a time.

For example:

```bash
cargo run --release -- 3 4
```

should evaluate `ack(3, 4)`.

Recommended output:

```text
ack(3, 4) = 125
runtime_seconds = 0.000123
```

For failure due to overflow:

```text
ack(3, 126) = OVERFLOW
runtime_seconds = 0.000123
```

If the operating system terminates the process because of stack exhaustion, memory exhaustion, or an external timeout, the caller should be able to distinguish that from a successful result.

---

## 5. Measure runtime

Measure the wall-clock evaluation time using:

```rust
std::time::Instant
```

Measure only the Ackermann computation itself as closely as practical.

For example:

```rust
let start = Instant::now();
let result = ack(n, m);
let elapsed = start.elapsed();
```

Report time in seconds with sufficient precision.

Build and run performance experiments using:

```bash
cargo run --release -- ...
```

or directly execute the release binary.

Do not benchmark the debug build when determining the largest practical `m`.

---

## 6. Do not search for the limit inside one long-running process

Ackermann evaluation can grow extremely quickly in:

- call count;
- recursion depth;
- runtime;
- result magnitude.

A single overly ambitious call can:

- overflow the integer type;
- overflow the Rust thread stack;
- consume excessive CPU time;
- terminate the process.

Therefore, determine the practical limit using **one operating-system process per `(n, m)` value**.

Do not run an unbounded loop such as:

```rust
loop {
    m += 1;
    println!("{}", ack(4, m));
}
```

inside the same process.

A stack overflow can abort the process and prevent the program from recording earlier results cleanly.

---

## 7. Use a timeout for each experiment

Create a small driver script or equivalent test harness that launches the release executable separately for each value of `m`.

Use a conservative per-run timeout.

A default of approximately:

```text
10 seconds
```

per Ackermann evaluation is suitable for the workshop.

The timeout should be easy to change.

For example, the experiment should behave conceptually as follows:

```text
for m = 1, 2, 3, ...
    run ack(n, m) in a child process
    wait at most TIMEOUT seconds

    if successful:
        record result and runtime
    else if arithmetic overflow:
        record overflow and stop
    else if timeout:
        record timeout and stop
    else if process crashes:
        record process failure and stop
```

Do this separately for:

```text
n = 3
n = 4
```

A Unix `timeout` command may be used when available, but a portable Python driver using `subprocess.run(..., timeout=...)` is preferable if Python is already available in the workshop environment.

Do not create a search process that can run forever.

---

## 8. Search procedure

For each of:

```text
ack(3, m)
ack(4, m)
```

start with `m = 1` and increase `m` by one.

Stop at the first value that cannot be successfully computed under the chosen criteria.

A value counts as **successfully computed** only when:

1. the process exits normally;
2. the implementation reports no arithmetic overflow;
3. the result is correct;
4. the computation finishes within the configured timeout.

Record:

- `n`;
- `m`;
- result;
- runtime;
- success/failure;
- reason for failure.

The requested answer is the largest successful `m` immediately before the first failure.

Because this depends on:

- integer representation;
- implementation;
- stack size;
- CPU;
- compiler;
- optimization level;
- timeout;

do not hard-code a supposedly universal maximum.

Measure it on the current machine.

---

## 9. Distinguish mathematical, numeric, and practical limits

The report must clearly distinguish three different concepts.

### 9.1 Mathematical definition

The Ackermann function is mathematically defined for every pair of nonnegative integers.

There is no mathematical maximum `m`.

### 9.2 Numeric representation limit

A fixed-width Rust integer can represent only a finite range.

For example, if `u128` is used, some Ackermann values will exceed that range even if they could theoretically be computed with arbitrary-precision integers.

Do not confuse integer overflow with an inherent limitation of the Ackermann function.

### 9.3 Practical computational limit

The direct recursive algorithm may become impractical before the numerical result exceeds the integer type.

Possible reasons include:

- excessive recursive calls;
- stack overflow;
- timeout;
- process termination.

Report the actual reason encountered.

---

## 10. `ack(3, m)` sanity check

For small values, compare the recursive result with:

```text
ack(3, m) = 2^(m + 3) - 3
```

This identity is useful to verify correctness.

Do **not** replace the recursive implementation with this formula for the experiment.

The exercise is intended to measure the behavior of the Ackermann recurrence.

If the recursive implementation fails for an `m` whose closed-form result would still fit numerically, report that as a practical recursion/runtime limitation.

---

## 11. `ack(4, m)` sanity check

Useful known values include:

```text
ack(4, 0) = 13
ack(4, 1) = 65533
```

The next value grows dramatically.

Do not assume that because the final integer might be representable using an arbitrary-precision type, the direct recursive computation will be practical.

Do not attempt arbitrarily large `ack(4, m)` values without the per-process timeout.

---

## 12. Optional arbitrary-precision extension

After the required fixed-width implementation and experiment are complete, an optional extension may use `num-bigint` to explore the distinction between arithmetic overflow and computational infeasibility.

If this extension is implemented:

- keep the original recurrence semantics;
- keep the timeout protection;
- report it separately from the required experiment;
- do not replace the required implementation;
- do not claim that arbitrary precision makes large Ackermann evaluations practical.

This extension is optional.

---

## 13. Stack considerations

The direct recursive definition can produce deep or extremely large recursion trees.

Do not use arbitrary unsafe stack manipulation.

If stack exhaustion is encountered, report it as part of the experiment.

An optional secondary experiment may run the computation in a spawned Rust thread with an explicitly chosen stack size using:

```rust
std::thread::Builder::new().stack_size(...)
```

If this is attempted:

- document the stack size;
- keep the external timeout;
- do not choose an excessively large stack;
- report results separately.

The baseline result should use the normal implementation/environment unless the repository instructions specify otherwise.

---

## 14. Suggested project structure

Adapt to the existing repository rather than creating unnecessary files.

A reasonable structure is:

```text
src/
  main.rs
  ackermann.rs

tests/
  ackermann.rs

scripts/
  find_ackermann_limit.py
```

Possible responsibilities:

### `src/ackermann.rs`

Contains `pub fn ack(...)` and related error/result types.

### `src/main.rs`

Contains command-line parsing, timing, and result formatting.

### `tests/ackermann.rs`

Contains correctness tests.

### `scripts/find_ackermann_limit.py`

Runs one child process per `(n,m)` pair with a timeout and records the largest successful value.

---

## 15. Error handling

Prefer explicit error handling rather than panicking for expected conditions such as arithmetic overflow.

For example, define an error enum or use `Option<u128>` if that remains clear.

The CLI should return a nonzero exit code when evaluation fails.

Suggested meanings:

```text
0  success
2  invalid command-line input
3  arithmetic overflow
```

Timeout and process-crash conditions will usually be identified by the external driver.

Do not rely on parsing Rust panic messages as normal control flow.

---

## 16. Output of the experiment

Produce a table similar to:

```text
n  m  result   runtime_s   status
3  1  13       0.000001    success
3  2  29       0.000002    success
...
3  K  ...      ...         success
3  K+1         ...         timeout

4  1  65533    ...         success
4  2            ...         timeout
```

The exact values of `K` must come from the actual experiment.

At the end, print a concise summary:

```text
Largest successful m for ack(3,m): <value>
Largest successful m for ack(4,m): <value>

Limit criterion: <timeout> seconds per run
Integer type: <type>
Build: release
```

Also report the first failed value and why it failed.

Example:

```text
First failed ack(4,m): m=2
Reason: timeout after 10 seconds
```

Do not report a maximum without stating the timeout and integer type used.

---

## 17. Tests for invalid input

The CLI should reject:

- missing arguments;
- negative values represented as text;
- nonnumeric values;
- extra malformed arguments.

Examples that should fail cleanly:

```bash
cargo run --release --
cargo run --release -- -1 2
cargo run --release -- 3 -1
cargo run --release -- foo 2
```

---

## 18. Code quality

Follow the repository's existing Rust conventions.

Before finishing, run:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test
```

If formatting is required:

```bash
cargo fmt
```

then rerun all checks.

Do not suppress legitimate Clippy warnings simply to make the command pass.

---

## 19. Reproducibility

Record enough environment information to make the experiment interpretable.

At minimum capture:

```bash
rustc --version
cargo --version
```

If straightforward, also record:

- operating system;
- CPU architecture;
- timeout used;
- integer type;
- whether the release build was used.

Do not spend significant effort collecting hardware details that are not relevant to the exercise.

---

## 20. README / report

Add a short section to the appropriate README or create a concise result file such as:

```text
ACKERMANN_RESULTS.md
```

Include:

1. the implementation approach;
2. the integer type;
3. the timeout;
4. the Rust version;
5. the successful `(n,m)` measurements;
6. the largest successful `m` for `n=3`;
7. the largest successful `m` for `n=4`;
8. the first failure for each and its reason;
9. any stack or overflow observations.

Do not invent results before running the experiment.

---

## 21. Definition of done

The task is complete only when:

1. the Ackermann recurrence is implemented correctly in Rust;
2. small known values pass automated tests;
3. arithmetic overflow is detected rather than wrapped;
4. a release-mode CLI can evaluate one `(n,m)` pair;
5. runtime is measured;
6. the limit search runs each value in a separate process;
7. every experimental run has a finite timeout;
8. `ack(3,m)` is tested for increasing `m`;
9. `ack(4,m)` is tested for increasing `m`;
10. the largest successful `m` for each is measured, not guessed;
11. the first failed `m` and reason are recorded;
12. mathematical, numeric, and practical limits are distinguished;
13. `cargo fmt --check` passes;
14. Clippy passes with warnings treated as errors;
15. all tests pass;
16. the final Git diff contains only intentional changes.

Before finishing, inspect:

```bash
git status
git diff
```

Then summarize:

- files changed;
- implementation strategy;
- test results;
- timeout used;
- largest successful `m` for `ack(3,m)`;
- largest successful `m` for `ack(4,m)`;
- first failure for each;
- reason for each failure.
