"""Play an event with a strategy that lives anywhere.

The bot template runs itself, but a strategy kept in its own project, renamed,
or split across files may have no argument block of its own. This runs any of
them:

    python -m hiddengems.play --strategy src/my_bot.py:Hunter --server URL --name 'Gem Goblin'
"""
import argparse
import asyncio
import os
from .sdk import MappingBot, Refused, load_strategy, run_workshop


def main():
    parser = argparse.ArgumentParser(description='Play every round this credential is seated in.')
    parser.add_argument('--strategy', default='my_bot.py',
                        help='Strategy file, optionally FILE:CLASS (default my_bot.py)')
    parser.add_argument('--server', default=os.environ.get('HIDDENGEMS_SERVER', 'http://127.0.0.1:8765'),
                        help='Arena URL (default: $HIDDENGEMS_SERVER, else a local server)')
    parser.add_argument('--token', help='Your credential (default: $HIDDENGEMS_TOKEN)')
    parser.add_argument('--name', help='How you are shown in the arena and the standings')
    parser.add_argument('--poll', type=float, default=2.0, help='Seconds between lobby checks')
    parser.add_argument('--once', action='store_true', help='Play one round, then exit')
    parser.add_argument('--example', action='store_true', help='Use the bundled mapping example')
    args = parser.parse_args()
    # Either credential variable is accepted, and a token copied from a sheet may
    # carry whitespace.
    token = (args.token or os.environ.get('HIDDENGEMS_TOKEN')
             or os.environ.get('HIDDENGEMS_BOT_TOKEN') or '').strip()
    if not token:
        parser.error('Set HIDDENGEMS_TOKEN (or HIDDENGEMS_BOT_TOKEN), or pass --token')
    try:
        strategy = MappingBot if args.example else load_strategy(args.strategy)
    except (FileNotFoundError, ValueError) as problem:
        raise SystemExit(str(problem))
    try:
        asyncio.run(run_workshop(args.server, token, strategy, name=args.name, poll=args.poll,
                                 once=args.once, announce=lambda line: print(line, flush=True)))
    except Refused as refused:
        raise SystemExit(f'The server refused this client: {refused}')
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
