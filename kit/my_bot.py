"""Python bot template: customize MyBot, then see README.md to connect it."""

import argparse
import asyncio
import json
import os

from hiddengems.sdk import BotStrategy, Refused, run_bot, run_workshop


class MyBot(BotStrategy):
    def initialize(self, message):
        super().initialize(message)
        # Add persistent map, target and energy-planning state here.

    def choose_scan(self, turn):
        return 1 if turn["self"]["energy"] else 0

    def choose_move(self, observation):
        x, y = observation["self"]["position"]
        floor = {
            tuple(c["position"]) for c in observation["terrain"] if c["kind"] == "floor"
        }
        blocked = {tuple(b["position"]) for b in observation["bots"]}
        # Prefer a rotating direction; replace this with persistent map/energy planning.
        options = [
            ("N", (x, y - 1)),
            ("E", (x + 1, y)),
            ("S", (x, y + 1)),
            ("W", (x - 1, y)),
        ]
        shift = (observation["turn"] // 5 + observation["self"]["id"]) % 4
        for direction, cell in options[shift:] + options[:shift]:
            if (
                cell in floor
                and cell not in blocked
                and observation["self"]["energy"] >= 1
            ):
                return {"direction": direction, "distance": 1}
        return {"direction": "WAIT", "distance": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Play Hidden Gems with the strategy in this file."
    )
    parser.add_argument(
        "--server",
        default=os.environ.get("HIDDENGEMS_SERVER", "http://127.0.0.1:8765"),
        help="Arena URL (default: $HIDDENGEMS_SERVER, else a local server)",
    )
    parser.add_argument(
        "--match",
        help="One match to play; omit it to join every round you are seated in",
    )
    parser.add_argument(
        "--name", help="How you are shown in the arena and the standings"
    )
    parser.add_argument("--once", action="store_true", help="Play one round, then exit")
    args = parser.parse_args()
    # Tokens are copied from a sheet or an email, so tolerate stray whitespace.
    token = (
        os.environ.get("HIDDENGEMS_TOKEN")
        or os.environ.get("HIDDENGEMS_BOT_TOKEN")
        or ""
    ).strip()
    if not token:
        parser.error("Set HIDDENGEMS_TOKEN (or HIDDENGEMS_BOT_TOKEN)")
    try:
        if args.match:
            result = asyncio.run(
                run_bot(args.server, args.match, token, MyBot(), args.name or "My bot")
            )
            print(json.dumps(result))
        else:
            # No match given: the server tells this token which round to join next.
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
