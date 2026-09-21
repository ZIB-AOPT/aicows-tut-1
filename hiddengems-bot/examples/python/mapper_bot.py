"""Connect the example mapper, or replace MappingBot with your own strategy."""
import argparse
import asyncio
import json
import os
from hiddengems.sdk import MappingBot, Refused, run_bot, run_workshop

parser = argparse.ArgumentParser()
parser.add_argument('--server', default='http://127.0.0.1:8765')
parser.add_argument('--match', help='One match to play; omit it to join every round you are seated in')
parser.add_argument('--name', help='How you are shown in the arena and the standings')
parser.add_argument('--once', action='store_true', help='Play one round, then exit')
args = parser.parse_args()
# Tokens are copied from a sheet or an email, so tolerate stray whitespace.
token = (os.environ.get('HIDDENGEMS_TOKEN') or os.environ.get('HIDDENGEMS_BOT_TOKEN') or '').strip()
if not token:
    parser.error('Set HIDDENGEMS_TOKEN (or HIDDENGEMS_BOT_TOKEN) to this bot credential')
try:
    if args.match:
        print(json.dumps(asyncio.run(run_bot(args.server, args.match, token, MappingBot(),
                                             args.name or 'Example mapper'))))
    else:
        # No match given: the server tells this token which round to join next.
        asyncio.run(run_workshop(args.server, token, MappingBot, name=args.name,
                                 once=args.once, announce=lambda line: print(line, flush=True)))
except Refused as refused:
    raise SystemExit(f'The server refused this client: {refused}')
except KeyboardInterrupt:
    pass
