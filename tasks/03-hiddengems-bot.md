# OpenCode Task: Write a Hidden Gems Arena Bot

## Goal

Write a competition bot for the **Hidden Gems Arena** in **Python, Rust or
C++**, using the bot kit in `hiddengems-bot/`.

The bot must:

1. connect to an arena server that runs on a different machine;
2. decide, once per turn, how much sensing to buy and where to move;
3. maintain its own map and gem memory across the whole match;
4. collect as many gem points as possible in 1500 turns;
5. come with automated tests that run without an arena.

All three languages speak the same protocol and compete on equal terms. Pick
one; there is no advantage in submitting more than one bot.

---

## 1. What you are given

The `hiddengems-bot/` folder is the client-side half of the arena project. The
game engine, map generator, server, spectator UI and replay verifier are **not**
in this repository; they run on the operator's machine.

| Path | Contents |
|---|---|
| `hiddengems-bot/hiddengems/sdk.py` | Python SDK: `BotStrategy`, `MappingBot`, `run_bot` |
| `hiddengems-bot/hiddengems/config.py` | public constants and defaults |
| `hiddengems-bot/examples/python/bot.py` | minimal Python strategy |
| `hiddengems-bot/examples/python/mapper_bot.py` | the reference mapper |
| `hiddengems-bot/examples/rust/` | complete Rust client; strategy in `src/bot.rs` |
| `hiddengems-bot/examples/cpp/` | complete C++ client; strategy in `src/bot.hpp` |
| `hiddengems-bot/docs/current-rules.md` | authoritative mechanics |
| `hiddengems-bot/docs/protocol.md` | wire format, deadlines, failure handling |
| `hiddengems-bot/docs/tournament.md` | round format and exact scoring |

`hiddengems-bot/docs/` is authoritative. This file is a working summary; where
the two disagree, the documents win.

Do not edit anything under `hiddengems-bot/`. It is a verbatim copy of the
arena project and is deliberately excluded from this repository's Ruff and
Pyright configuration. Your own code lives outside it and **is** checked.

---

## 2. Rules of the game

These rules are the same whichever language you choose.

### 2.1 Arena and match

- The arena is **120 × 80** cells, including a one-cell wall boundary.
  Coordinates are `[x, y]`, zero-based from the upper left; `+x` is east,
  `+y` is south.
- A match has **1 to 64 bots** (usually 50) and **1500 turns, numbered
  0 to 1499**.
- All bots start simultaneously on distinct floor cells. Bots have **solid
  bodies**: you cannot move through another bot, even a disconnected one.
- Four map families are used, all with corridors, corners and doorways at
  least **two cells wide**; walls may be one cell thick.

| Map | Shape |
|---|---|
| `rooms` | open center, four hollow buildings, each with one two-wide doorway |
| `labyrinth` | dense connected maze, two-wide corridors, many dead ends |
| `exploration` | the same construction with many extra links and loops |
| `long-walls` | mostly open floor with six long straight walls, passable at both ends |

A championship is 12 matches, three per family. A round with winning score `W`
gives an entrant with score `S` exactly `1000 * S / W` championship points, so
being consistently close to the winner matters as much as winning a round.

### 2.2 Energy

- You start with **zero** energy.
- **+3 energy** is added before every turn's decisions.
- There is **no storage cap**, and leftover energy is worth **no points**.
- Both the scan and the move in a turn are paid from the same reserve, in that
  order.

Over a full match you receive 4500 energy. Every unit you do not spend is
wasted, and every unit you spend badly is a gem you did not reach.

### 2.3 The turn cycle

At the start of turn `t` the server, in this order:

1. removes every gem whose expiry is at or before `t`;
2. evaluates that turn's scheduled gem spawn, if there is one;
3. adds 3 energy to every bot;
4. sends you a `turn` message and waits for your **scan** decision;
5. sends you the `observation` you paid for and waits for your **move**.

Both phases share one deadline, **250 ms by default**, which includes network
return time. A missing scan reply counts as `n = 0`; a missing move reply counts
as `WAIT`. More than 128 cumulative invalid or stale messages disables the slot,
so never send a second reply for the same phase.

### 2.4 Sensing is paid

Sensing is the only way to learn about the world, and it costs energy:

- choose an integer `n >= 1` for a **Manhattan radius of `5 * n`**, at a cost of
  `ceil(n ** 1.5)`;
- `n = 0` skips sensing, costs nothing, and returns an empty observation;
- a scan you cannot afford costs nothing and returns an empty observation with
  `scan_error` set.

| `n` | 1 | 2 | 3 | 4 | 8 |
|---|---:|---:|---:|---:|---:|
| radius | 5 | 10 | 15 | 20 | 40 |
| cost | 1 | 3 | 6 | 8 | 23 |

What a scan returns, for cells within Manhattan distance `5 * n` (inclusive):

- `terrain`: `{"position": [x, y], "kind": "floor" | "wall"}`, but only along a
  clear line of sight. An intervening wall hides what is behind it; a wall at
  the target cell is itself visible. Other bots do not block the view.
- `bots`: `{"id": ..., "position": [x, y]}` for opponents in line of sight.
  Never their energy or score.
- `gems`: `{"id": ..., "position": [x, y], "ttl": ...}`. **Gem radar ignores
  walls**, so gems are detected inside the radius even through solid rock.

These are always free, in both the `turn` and the `observation` message:

- your own `position`, `energy`, `score` and `captures`;
- `feedback` from your previous move: the distance actually travelled, whether
  you were `blocked`, and a reason. The type of the obstruction is **not**
  revealed.

Cells you actually traversed are known floor, so movement feedback maps the
world for free.

### 2.5 Movement

A move is one cardinal direction and an integer distance:

```json
{"type": "move", "turn": 17, "direction": "E", "distance": 3}
```

- Directions are `N`, `E`, `S`, `W` and `WAIT`. `WAIT` requires distance 0.
- Distance `d` costs **`d ** 2`** energy, taken from what is left after the scan.
- You cannot turn during a move, pass through a wall, or pass through a bot.
- The declared cost is **charged in full before the move resolves**. If you are
  blocked after one cell of a five-cell burst, you still paid 25.
- An invalid or unaffordable move silently becomes `WAIT`.

Quadratic cost is the central trade-off: five single steps cost 5 and take five
turns, one five-step burst costs 25 and takes one turn. Long bursts only pay off
for a gem that would otherwise expire or be taken first.

Conflicts are resolved deterministically. The `j`-th cell of a length-`d` burst
is entered at fraction `j / d` of the turn, ties are broken by a seeded rotating
initiative order, entering a still-occupied cell stops that burst permanently,
and swaps are blocked. Arrival order decides who gets a contested gem.

### 2.6 Gems and scoring

- The map starts empty. Turns 0 to 9 have no spawns.
- One spawn is attempted on turns **10, 13, 16, ..., 1498** — 497 attempts.
- Each attempt has a pre-assigned floor cell and a lifetime of **60, 180 or
  300** turns (166 / 165 / 166 attempts, shuffled unpredictably).
- An attempt is **skipped** — never retried or relocated — if 20 gems are
  already active, a bot stands on the cell, or a gem is already there.
- A gem born on turn `b` with lifetime `L` is active on turns `b` through
  `b + L - 1`. Its remaining lifetime on turn `t` is `b + L - t`.
- **Collecting a gem scores its remaining lifetime.** A gem is collected
  automatically by entering its cell, including as an intermediate cell of a
  longer burst, so one move can sweep several gems for one movement cost.
- Uncollected gems at the end of the match score nothing.

A gem therefore decays by one point per turn. A 300-turn gem is worth 300 the
turn it appears and 1 on its last turn. Distance is paid twice: in energy, and
in the points the gem loses while you travel.

Everything you know about gems comes from your own paid radar. There are no
global announcements, and a gem you saw earlier may already have been taken by
somebody else — but its **expiry turn is reliable**, because lifetimes never
change.

### 2.7 What does not exist

Do not plan around these; they were tested and removed:

- trading score for energy;
- global gem birth or collection announcements;
- directional search rays, energy pills, pass-through movement, elimination;
- free world sensing of any kind.

---

## 3. Choose a language

| | Python | Rust | C++ |
|---|---|---|---|
| Template | `examples/python/bot.py` | `examples/rust/` | `examples/cpp/` |
| Transport | `hiddengems.sdk.run_bot` (aiohttp) | tungstenite + rustls | Boost.Beast + OpenSSL |
| JSON | `dict` | `serde_json::Value` | `nlohmann::json` |
| Already installed here | yes, through `uv sync` | yes, `rustup` toolchain | needs CMake 3.24+, OpenSSL, Boost.Beast |
| Covered by `./scripts/check.sh` | yes | yes, once a workspace exists | no, add your own commands |

Python is the shortest route to a working bot and the only language with a
worked reference strategy (`MappingBot`). Rust and C++ give more headroom if
your planner becomes expensive, but the 250 ms budget is generous for a
120 × 80 grid and raw speed is rarely what decides a match.

The C++ toolchain is the heaviest: CMake fetches Boost 1.92 on first build if
it is not installed, which is a substantial download. Confirm the prerequisites
before committing to it.

---

## 4. Where your code goes

Never edit the kit. Create your own project next to it, at the repository root.

### 4.1 Python

Add a new package at the **repository root**, next to `hiddengems-bot/`, not
inside it. It imports the SDK that `uv sync` already installed.

```text
aicows-tut-1/
├── hiddengems-bot/       # the kit: read-only
├── mybot/
│   ├── __init__.py
│   ├── strategy.py       # your strategy class
│   └── __main__.py       # command-line entry point
└── tests/
    └── test_mybot.py
```

This location is already wired up: Ruff and Pyright check `mybot/` and `tests/`,
`[tool.pytest.ini_options] pythonpath = ["."]` lets the tests import `mybot`,
and Pyright's `extraPaths` resolves `import hiddengems...` to the kit's sources.
Nothing in `pyproject.toml` needs changing unless you add a dependency.

```bash
uv sync
export HIDDENGEMS_TOKEN='the-token-you-were-given'
uv run mybot --server https://ARENA_HOST --name 'My bot'
```

There is no match ID to pass: the lobby seats your token in every round and the
client plays them as they open. Leave it running for the whole event.

`mybot = "mybot.__main__:main"` is already registered in `[project.scripts]`,
so the command exists as soon as the package does; run `uv sync` once after
creating it. Without such an entry `uv run mybot` falls back to executing the
`mybot/` **directory**, which puts that directory on `sys.path` instead of the
repository root and breaks `import mybot.strategy`. `uv run python -m mybot`
works either way.

### 4.2 Rust

Copy the template out of the kit, then edit your copy:

```bash
cp -r hiddengems-bot/examples/rust mybot
```

Rename the package in `mybot/Cargo.toml` from `hiddengems-bot` to `mybot`, and
add a workspace manifest at the repository root so `./scripts/check.sh` finds
your crate:

```toml
# Cargo.toml
[workspace]
members = ["mybot"]
exclude = ["hiddengems-bot/examples/rust"]
resolver = "2"
```

The `exclude` line keeps the kit's untouched copy out of your checks.

```bash
cargo build --release --locked
export HIDDENGEMS_BOT_TOKEN='the-slot-token-you-were-given'
./target/release/mybot --server http://ARENA_HOST:8765 --match MATCH_ID --name 'My bot'
```

### 4.3 C++

Copy the template out of the kit, then edit your copy:

```bash
cp -r hiddengems-bot/examples/cpp mybot
```

Rename the project and executable in `mybot/CMakeLists.txt`.

```bash
cmake -S mybot -B mybot/build -DCMAKE_BUILD_TYPE=Release
cmake --build mybot/build --config Release --parallel 2
export HIDDENGEMS_BOT_TOKEN='the-slot-token-you-were-given'
./mybot/build/mybot --server http://ARENA_HOST:8765 --match MATCH_ID --name 'My bot'
```

On macOS, add `-DOPENSSL_ROOT_DIR="$(brew --prefix openssl@3)"` if CMake cannot
find OpenSSL. Add `mybot/build/` to `.gitignore`.

### In every language

The operator gives you a server URL and **one** participant token. The token
must travel in the environment (`HIDDENGEMS_TOKEN`, or `HIDDENGEMS_BOT_TOKEN`
for the native clients), never on the command line and never in a URL. Do not
commit it.

The Python SDK adds a lobby mode: `run_workshop` asks the server which round
this token is seated in next, so a Python client needs no match ID and can be
left running for the whole event. The Rust and C++ templates have no lobby
client — they take `--match MATCH_ID` for one match, and the operator hands you
that ID per round.

---

## 5. The strategy interface

Every template exposes the same three hooks, and the surrounding client handles
the handshake, the message loop and the final result. The object is created once
and lives for the whole match, so anything you store on it persists.

| Hook | Receives | Returns |
|---|---|---|
| `initialize` | the `init` message: `config`, `self` | nothing |
| `choose_scan` | the `turn` message: free own state | the integer `n` |
| `choose_move` | the `observation` you paid for | direction and distance |

### 5.1 Python

`run_bot` is duck-typed: any object with the three methods works. Write a plain
class in `mybot/strategy.py`.

```python
class MyBot:
    def initialize(self, message):
        self.config = message["config"]
        self.my_id = message["self"]["id"]
        self.width = self.config["width"]
        self.height = self.config["height"]
        self.floor = {}
        self.gems = {}

    def choose_scan(self, turn) -> int:
        # turn["turn"], turn["self"]["energy"], turn["self"]["feedback"]
        return 1 if turn["self"]["energy"] >= 1 else 0

    def choose_move(self, observation) -> dict:
        # observation adds "terrain", "bots", "gems", "radius", "scan_error"
        return {"direction": "WAIT", "distance": 0}
```

You may subclass `hiddengems.sdk.BotStrategy` instead, as the kit's examples do,
but Pyright then reports `choose_scan` as an incompatible override: the SDK's
stub returns the literal `0`, so any wider return type fails the check. A plain
class avoids that and costs one line.

The entry point hands your class to `run_workshop`, which claims your display
name, waits for the lobby to seat you, and starts a **fresh strategy object for
each round** — so pass the class, not an instance:

```python
import argparse
import asyncio
import os

from hiddengems.sdk import Refused, run_workshop

from mybot.strategy import MyBot


def main():
    parser = argparse.ArgumentParser(prog="mybot")
    parser.add_argument("--server", default="http://127.0.0.1:8765")
    parser.add_argument("--name", help="How you are shown in the standings")
    parser.add_argument("--once", action="store_true", help="Play one round, then exit")
    args = parser.parse_args()
    token = (os.environ.get("HIDDENGEMS_TOKEN") or "").strip()
    if not token:
        parser.error("Set HIDDENGEMS_TOKEN")
    try:
        asyncio.run(
            run_workshop(
                args.server,
                token,
                MyBot,
                name=args.name,
                once=args.once,
                announce=lambda line: print(line, flush=True),
            )
        )
    except Refused as refused:
        raise SystemExit(f"The server refused this client: {refused}")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
```

Read `hiddengems-bot/examples/python/mapper_bot.py` and the `MappingBot` class
in the SDK before starting. `MappingBot` is a complete, compact bot: it keeps a
known-cell map, tracks gem expiries, runs a breadth-first search over known
floor, and falls back to frontier exploration. It is the baseline to beat, not
a ceiling.

### 5.2 Rust

Edit `mybot/src/bot.rs`. `main.rs` already owns argument parsing,
authentication, WebSockets and JSON dispatch; you should not need to touch it.

```rust
use serde_json::{json, Value};
use std::collections::HashMap;

#[derive(Default)]
pub struct MyBot {
    pub config: Value,
    pub floor: HashMap<(i64, i64), bool>,
    pub gems: HashMap<u64, ((i64, i64), u64)>,
}

impl MyBot {
    pub fn initialize(&mut self, message: &Value) {
        self.config = message["config"].clone();
    }

    pub fn choose_scan(&mut self, turn: &Value) -> u64 {
        u64::from(turn["self"]["energy"].as_u64().unwrap_or(0) > 0)
    }

    pub fn choose_move(&mut self, observation: &Value) -> Value {
        let _ = observation;
        json!({"direction": "WAIT", "distance": 0})
    }
}
```

Never `unwrap` on data from the wire in a way that can panic: a panic ends your
match. Use `as_u64().unwrap_or(0)` and friends, and keep the bot alive.

### 5.3 C++

Edit `mybot/src/bot.hpp`. `main.cpp` owns the transport and protocol.
`MyBot` is header-only, which makes it easy to test.

```cpp
#pragma once
#include <nlohmann/json.hpp>
#include <map>
#include <utility>

using Json = nlohmann::json;

class MyBot {
public:
    Json config;
    std::map<std::pair<int, int>, bool> floor;

    void initialize(const Json& message) {
        config = message.at("config");
    }

    int choose_scan(const Json& turn) {
        return turn.at("self").at("energy").get<int>() > 0 ? 1 : 0;
    }

    Json choose_move(const Json& observation) {
        (void)observation;
        return {{"direction", "WAIT"}, {"distance", 0}};
    }
};
```

Use `value(key, default)` rather than `at(key)` for fields that may be absent,
such as `scan_error`, and let no exception escape a hook.

---

## 6. Requirements

These apply in every language. Your bot must:

1. keep a **persistent map** of known floor and wall cells, built from every
   observation and from movement feedback;
2. keep a **gem memory** with each gem's position and expiry turn, and drop
   entries that have expired or that a fresh scan proves are gone;
3. **plan routes over known floor**, not straight-line Manhattan distance —
   a gem ten cells away through a wall may be forty cells of walking;
4. **budget energy explicitly**, deciding both scan size and burst length
   against the remaining reserve;
5. **choose targets by value**, comparing the points a gem will still be worth
   on arrival against the energy and turns needed to get there;
6. **explore** when nothing is worth chasing, rather than standing still;
7. never crash: a malformed or empty observation, `scan_error`, a blocked move
   or zero energy must all be handled, and no hook may panic, throw or hang;
8. **respect the deadline** — every decision must return well inside 250 ms on
   a 120 × 80 map.

### Think about

- **Scan cadence.** Radius 5 for 1 energy every turn, or radius 15 for 6 energy
  every six turns? Past experiments found no single best answer: the winning
  cadence changed when opponents' scan phases were staggered. Do not hard-code
  the example bot's schedule and assume it is optimal.
- **The opening.** You start with 0 energy and the first gem cannot appear
  before turn 10. Saving early and exploring cheaply is not obviously wrong.
- **Competition.** Other bots see the same gem. Being second to arrive scores
  nothing and costs the whole trip. Opponent positions are in every observation.
- **Sweeping.** One long burst through several gems pays `d ** 2` once.
- **Blocking.** Two bodies can seal a two-wide doorway; one cannot. Expect to
  be blocked and re-plan when `feedback["blocked"]` is true.

---

## 7. Test without an arena

The arena is not in this repository and will not be available while you work.
Test your strategy by calling the hooks directly with handcrafted messages. In
every language they are ordinary JSON values that you can build by hand.

Cover at least:

- a visible gem is approached, and reached when it is affordable;
- an expired gem is dropped from memory;
- zero energy produces a legal `WAIT`;
- an empty observation with `scan_error` set does not raise, panic or throw;
- `feedback["blocked"]` marks the blocking cell and changes the plan;
- the known map survives across turns;
- no returned move ever costs more energy than the bot holds.

A small deterministic harness that replays a scripted sequence of observations
and asserts the whole sequence of moves is worth more than many single-turn
tests.

### 7.1 Python

Put tests in `tests/`, run them with `uv run pytest`.

```python
from mybot.strategy import MyBot

CONFIG = {"width": 120, "height": 80, "turns": 1500}


def own(position, energy):
    return {"id": 0, "position": position, "energy": energy, "score": 0}


def make_bot():
    bot = MyBot()
    bot.initialize({"config": CONFIG, "self": own([10, 10], 0)})
    return bot


def test_walks_towards_a_visible_gem():
    bot = make_bot()
    bot.choose_scan({"turn": 20, "self": own([10, 10], 9)})
    floor = [{"position": [x, 10], "kind": "floor"} for x in range(10, 14)]
    move = bot.choose_move(
        {
            "turn": 20,
            "self": own([10, 10], 8),
            "radius": 5,
            "scan_cost": 1,
            "scan_error": None,
            "terrain": floor,
            "bots": [],
            "gems": [{"id": 3, "position": [13, 10], "ttl": 120}],
        }
    )
    assert move["direction"] == "E"
    assert 1 <= move["distance"] <= 3
```

The real `self` block also carries `captures` and `feedback`; add the fields
your strategy actually reads.

### 7.2 Rust

`bot.rs` belongs to a binary crate, so put unit tests in the same file and run
them with `cargo test`.

```rust
#[cfg(test)]
mod tests {
    use super::MyBot;
    use serde_json::json;

    fn own(x: i64, y: i64, energy: u64) -> serde_json::Value {
        json!({"id": 0, "position": [x, y], "energy": energy, "score": 0})
    }

    #[test]
    fn walks_towards_a_visible_gem() {
        let mut bot = MyBot::default();
        bot.initialize(&json!({"config": {"width": 120, "height": 80}}));
        let observation = json!({
            "turn": 20,
            "self": own(10, 10, 8),
            "radius": 5,
            "scan_error": null,
            "terrain": [
                {"position": [11, 10], "kind": "floor"},
                {"position": [12, 10], "kind": "floor"},
            ],
            "bots": [],
            "gems": [{"id": 3, "position": [12, 10], "ttl": 120}],
        });
        let move_ = bot.choose_move(&observation);
        assert_eq!(move_["direction"], "E");
    }
}
```

### 7.3 C++

`bot.hpp` is header-only, so a test is a second executable that includes it.
Add it to your `CMakeLists.txt` and register it with `ctest`:

```cmake
enable_testing()
add_executable(mybot-tests tests/test_strategy.cpp)
target_link_libraries(mybot-tests PRIVATE nlohmann_json::nlohmann_json)
target_include_directories(mybot-tests PRIVATE src)
add_test(NAME strategy COMMAND mybot-tests)
```

```cpp
#include "bot.hpp"
#include <cassert>

int main() {
    MyBot bot;
    bot.initialize({{"config", {{"width", 120}, {"height", 80}}}});
    const Json observation = {
        {"turn", 20},
        {"self", {{"id", 0}, {"position", {10, 10}}, {"energy", 8}, {"score", 0}}},
        {"radius", 5},
        {"terrain", {{{"position", {11, 10}}, {"kind", "floor"}}}},
        {"bots", Json::array()},
        {"gems", {{{"id", 3}, {"position", {11, 10}}, {"ttl", 120}}}},
    };
    const Json move = bot.choose_move(observation);
    assert(move.at("direction") == "E");
    return 0;
}
```

Run with `ctest --test-dir mybot/build --output-on-failure`.

---

## 8. Code quality

Your code is checked; the kit is not. Before finishing, run:

```bash
./scripts/check.sh
```

It runs Ruff, Pyright and pytest over the repository, and `cargo fmt`,
`cargo clippy -- -D warnings` and `cargo test` when a Cargo workspace exists
outside the kit. It does **not** build or test C++: if you chose C++, run your
CMake build and `ctest` yourself and report the commands.

Do not suppress legitimate Ruff, Pyright, pytest, `rustfmt`, Clippy or compiler
failures, and do not add your own package to the checks' exclusions.

Do not:

- modify anything under `hiddengems-bot/`;
- commit a bot token, a match ID or a server URL;
- commit build output (`target/`, `build/`);
- add a dependency without updating the matching lock file (`uv.lock`,
  `Cargo.lock`) intentionally;
- attempt to reach the arena's operator or spectator API — a bot token grants
  one slot and nothing else, and spectator data is the whole map;
- rely on any mechanic listed in section 2.7.

---

## 9. Definition of done

The task is complete only when:

1. the bot builds and its `--help` works in the language you chose;
2. the three hooks are implemented on your own copy of the strategy, with the
   kit left untouched;
3. map knowledge and gem memory persist across turns;
4. routes are planned over known floor, not straight-line distance;
5. scan size and move distance are both chosen against the energy reserve;
6. targets are chosen by value on arrival, not by raw proximity;
7. the bot explores when no target is worth chasing;
8. every returned move is legal and affordable;
9. empty observations, scan errors, blocked moves and zero energy are handled
   without a crash, panic or uncaught exception;
10. decisions stay well inside the 250 ms deadline;
11. tests cover targeting, memory, energy limits and failure handling, and run
    without an arena;
12. `./scripts/check.sh` passes, plus the C++ build and `ctest` if you chose C++;
13. `git status` and `git diff` show only intentional changes.

Before finishing, summarize:

- the language chosen and why;
- files changed;
- the scan policy and why;
- the movement and target-selection policy and why;
- how energy is budgeted;
- verification commands run and test results;
- known weaknesses of the strategy.
