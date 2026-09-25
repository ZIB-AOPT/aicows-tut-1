# Hidden Gems: write a bot

Your credential and the arena URL are given to you at the event. The credential
lasts the whole day and seats you in every round; you never need a match ID.

## 1. Install

With [uv](https://docs.astral.sh/uv/):

```sh
uv venv && uv pip install -e .
```

Or with the Python you already have:

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
```

## 2. Write your strategy

`my_bot.py` holds your bot. Edit `initialize`, `choose_scan` and `choose_move`;
everything else is the client.

Keep the block at the bottom of the file and `python my_bot.py` runs it. If you
would rather restructure — your own project, a different file name, several
files — drop the block and run your class through the client instead:

```sh
.venv/bin/python -m hiddengems.play --strategy kit/my_improved_bot.py:MyImprovedBot
```

## 3. Check it without a server

```sh
.venv/bin/python -m hiddengems.selfcheck my_bot.py
```

This feeds your strategy the messages the protocol defines and reports crashes,
actions the server would reject, and decisions slower than the deadline. It does
not play the game, so it says nothing about how well your bot scores.

## 4. Join the arena

Set the two things you are given, once per terminal:

```sh
export HIDDENGEMS_SERVER='https://gemrush.fun'
export HIDDENGEMS_TOKEN='your-credential'
.venv/bin/python my_bot.py --name 'Your name'
```

It waits for the next round, plays it, prints the result as one JSON line, and
waits for the round after that. Leave it running; edit your strategy between
rounds and restart it when you want the changes to take effect.

`--name` chooses how you appear in the arena and the standings. Names are unique,
so if yours is taken the client says so and you pick another. Both settings also
have flags: `--server` and `--token`.

## Other languages

`rust/` and `cpp/` hold standalone clients that speak the same protocol and need
no Python. Each has its own README. Edit `src/bot.rs` or `src/bot.hpp`.

## The rules

`PROTOCOL.md` is the reference: what a scan costs, what an observation contains,
how movement resolves, and what happens when you answer too late.
