# Hidden Gems bot kit

Everything needed to **write and run a Hidden Gems bot**, extracted from the
`hiddengems` project. The arena (engine, map generator, HTTP/WebSocket server,
spectator UI, replay verifier, tournament scheduler) is **not** part of this
folder; it is hosted on a different machine. A bot connects to it over
WebSockets, so nothing here has to execute game logic.

Protocol: `hidden-gems-2.0`. Arena: 120 × 80, 1–64 bots, 1500 turns.

## What is here

| Path | Purpose |
|---|---|
| `hiddengems/sdk.py` | Async client: `BotStrategy`, `MappingBot`, `run_bot` for one match, `run_workshop` for a whole event, and the `Refused` / `NameRefused` errors. Handles hello/init, the scan → observation → move loop, and the final result. |
| `hiddengems/config.py` | Public constants and defaults (`RULESET`, `WIDTH`, `HEIGHT`, `MAX_BOTS`, energy/gem/scan values). Unchanged copy of the server's public config. |
| `examples/python/` | Python templates: `bot.py` (minimal), `mapper_bot.py` (the built-in mapper) and `workshop_bot.py` (loads a strategy from any file and plays the whole event). |
| `examples/rust/`, `examples/cpp/` | Self-contained Rust and C++ clients with their own transport; edit `src/bot.rs` / `src/bot.hpp`. |
| `docs/current-rules.md` | Authoritative mechanics: movement, energy, paid sensing, map families, gem generation and scoring. |
| `docs/protocol.md` | Wire format, message schemas, deadlines, failure handling. |
| `docs/tournament.md` | Round format, exact scoring and tie-breaks. |
| `docs/insights.md` | Accepted design decisions and what past experiments do and do not establish. |

Only the operator runs the `/api/...` routes described in `docs/protocol.md`;
as an entrant you need the bot sections. Ignore references in the copied docs to
files that live in the arena repository (`tools/`, `docs/history/`, the server
setup commands in `docs/operations.md`). `docs/` predates lobby mode and does
not describe the `/api/lobby` routes the SDK uses; read `hiddengems/sdk.py`
for those.

## Python quick start

The kit has no environment of its own. It is a member of this repository's uv
workspace, so `uv sync` installs it, together with aiohttp, into the project
`.venv` at the repository root. The install is editable: changes under
`hiddengems/` and `examples/` take effect immediately.

```sh
uv sync                                   # once, from the repository root

export HIDDENGEMS_TOKEN='your-participant-token'
uv run python hiddengems-bot/examples/python/bot.py \
    --server https://ARENA_HOST --name 'My bot'
```

The operator supplies a server URL and **one** participant token. The token
goes in the environment — `HIDDENGEMS_TOKEN`, or `HIDDENGEMS_BOT_TOKEN` for the
Rust and C++ clients — and travels in an `Authorization` header, never on the
command line or in a URL.

With no `--match`, the client asks the lobby which round this token is seated in
next, announces each one, and keeps playing until you stop it: leave it running
for the whole event. `--once` plays a single round and exits. Pass
`--match MATCH_ID` to play one specific match and print its result as one JSON
line; that is the only mode the Rust and C++ clients have.

## Writing a strategy

Implement three hooks; state on the object persists between turns. Subclassing
`BotStrategy` is optional for `run_bot` and `run_workshop`, which only call the
methods, but `workshop_bot.py --strategy` discovers strategies by subclass, so
inherit from it if you want that loader to find your class.

```python
class MyBot(BotStrategy):
    def initialize(self, message): ...      # message['config'], message['self']
    def choose_scan(self, turn): ...        # -> n; radius 5n, cost ceil(n**1.5)
    def choose_move(self, observation): ... # -> {'direction': 'N|E|S|W|WAIT', 'distance': d}
```

Per turn the server adds 3 energy, asks for a scan, sends the observation it
bought, then asks for a move. A move of distance `d` in one cardinal direction
costs `d²` from the energy left after the scan. Own position, energy and
movement feedback are free; terrain, opponents and gems only arrive through a
paid scan. Gem radar sees through walls, terrain and opponents need line of
sight. A collected gem is worth its remaining lifetime.

`run_workshop` takes the strategy **class**, not an instance, and builds a new
one for every round, so per-match memory starts clean and anything you want to
carry across rounds has to be class-level or external.

Keep each decision inside the phase deadline (250 ms by default, covering
network return time). Long planning does not belong in the response path.

## Notes on the copies

- `hiddengems/sdk.py` and `examples/python/` come from a later arena build than
  the rest of this folder: they add lobby mode (`run_workshop`, `Refused`,
  `workshop_bot.py`). `hiddengems/config.py` and all of `docs/` are still the
  byte-identical earlier copies, so the documented protocol lags the SDK.
  Refresh the whole folder together when the arena publishes a new ruleset.
- The only edit made here is the one-line docstring in `hiddengems/__init__.py`.
- `examples/rust/` and `examples/cpp/` do not use the Python SDK and can be
  built and shipped on their own.
- The per-language READMEs describe the upstream standalone setup (`python3 -m
  venv`, `pip install -r requirements.lock`) and, in `examples/python/`, still
  show the pre-lobby `--match MATCH_ID` flow. Inside this repository, use
  `uv sync` and `uv run` instead. `requirements.txt` and `requirements.lock`
  are kept only for running a Python bot outside this repository; within it,
  `uv.lock` is the single source of truth.
