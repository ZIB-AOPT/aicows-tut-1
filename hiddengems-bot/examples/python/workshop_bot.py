"""Workshop client: one permanent token, joins every round by itself.

Put your strategy in a file (start from bot.py), then leave this running:

    export HIDDENGEMS_TOKEN='hg_your-token'
    python workshop_bot.py --server https://arena.example.com --strategy my_bot.py --name 'Gem Goblin'

Running `python my_bot.py` directly does the same thing, as long as the file
keeps the argument block that bot.py ends with.
"""
import argparse
import asyncio
import importlib.util
import inspect
import os
from pathlib import Path
import sys
from hiddengems.sdk import BotStrategy, MappingBot, Refused, run_workshop


def load_strategy(reference):
    """Import PATH[:CLASS] and return the strategy class, so each match starts fresh."""
    path, _, wanted = reference.partition(':')
    path = Path(path).resolve()
    if not path.is_file():
        raise SystemExit(f'No strategy file at {path}')
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if wanted:
        return getattr(module, wanted)
    classes = [value for value in vars(module).values()
               if inspect.isclass(value) and issubclass(value, BotStrategy)
               and value.__module__ == spec.name]
    if len(classes) != 1:
        raise SystemExit(f'Name the class to use, for example {path.name}:MyBot')
    return classes[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default='http://127.0.0.1:8765')
    parser.add_argument('--strategy', default='my_bot.py',
                        help='Strategy file, optionally FILE:CLASS (default my_bot.py)')
    parser.add_argument('--token', help='Participant token (default: $HIDDENGEMS_TOKEN)')
    parser.add_argument('--name', help='Claim how you are shown in the arena and standings')
    parser.add_argument('--poll', type=float, default=2.0, help='Seconds between lobby checks')
    parser.add_argument('--once', action='store_true', help='Play one match, then exit')
    parser.add_argument('--example', action='store_true', help='Use the bundled mapping example')
    args = parser.parse_args()
    # The language templates use HIDDENGEMS_BOT_TOKEN; accept either name so one
    # credential works whichever client a participant starts from.
    credential = (args.token or os.environ.get('HIDDENGEMS_TOKEN')
                  or os.environ.get('HIDDENGEMS_BOT_TOKEN') or '').strip()
    if not credential:
        parser.error('Set HIDDENGEMS_TOKEN (or HIDDENGEMS_BOT_TOKEN), or pass --token')
    strategy = MappingBot if args.example else load_strategy(args.strategy)
    try:
        asyncio.run(run_workshop(args.server, credential, strategy, name=args.name,
                                 poll=args.poll, once=args.once,
                                 announce=lambda line: print(line, flush=True)))
    except Refused as refused:
        raise SystemExit(f'The server refused this client: {refused}')
    except KeyboardInterrupt:
        pass
