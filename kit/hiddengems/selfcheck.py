"""Check a strategy on its own, with no server and no arena.

This feeds a strategy the messages the protocol defines and reports what a real
match would punish: a crash, an action the server would reject, or a decision
slower than the deadline. It does not simulate the game, so it says nothing
about how well a strategy plays.

    python -m hiddengems.selfcheck my_bot.py
"""
import argparse
import random
import time
from .config import GameConfig, RULESET, HEIGHT, WIDTH
from .sdk import load_strategy

DIRECTIONS = ('N', 'E', 'S', 'W', 'WAIT')


def own_state(bot_id, position, energy, turn):
    return {'id': bot_id, 'position': list(position), 'energy': energy, 'score': turn//40,
            'captures': turn//40, 'feedback': {'distance': 0, 'blocked': False, 'reason': None}}


def observation(rng, turn, position, energy, radius):
    """A schema-correct paid observation. The world is invented, not simulated."""
    x, y = position
    terrain, gems, bots = [], [], []
    for dx in range(-radius, radius+1):
        for dy in range(-radius+abs(dx), radius-abs(dx)+1):
            cell = (x+dx, y+dy)
            if not (0 <= cell[0] < WIDTH and 0 <= cell[1] < HEIGHT):
                continue
            wall = cell[0] in (0, WIDTH-1) or cell[1] in (0, HEIGHT-1) or rng.random() < 0.12
            terrain.append({'position': list(cell), 'kind': 'wall' if wall else 'floor'})
            if not wall and rng.random() < 0.02:
                gems.append({'id': rng.randrange(10**6), 'position': list(cell),
                             'ttl': rng.choice([60, 180, 300])})
            elif not wall and rng.random() < 0.02:
                bots.append({'id': rng.randrange(1, 60), 'position': list(cell)})
    return {'type': 'observation', 'turn': turn, 'self': own_state(0, position, energy, turn),
            'radius': radius, 'scan_cost': 0, 'scan_error': None, 'terrain': terrain,
            'gems': gems, 'bots': bots, 'deadline_ms': 250}


def check(strategy_class, turns, deadline_ms, seed):
    rng = random.Random(seed)
    strategy = strategy_class()
    position, energy = (WIDTH//2, HEIGHT//2), 0
    problems, slowest, total = [], 0.0, 0.0
    config = GameConfig()
    strategy.initialize({'type': 'init', 'protocol': RULESET, 'match_id': '0'*16,
                         'config': config.public(), 'self': own_state(0, position, energy, 0)})
    for turn in range(turns):
        energy += 3
        message = {'type': 'turn', 'turn': turn, 'self': own_state(0, position, energy, turn),
                   'deadline_ms': deadline_ms}
        start = time.perf_counter()
        n = strategy.choose_scan(message)
        elapsed = time.perf_counter()-start
        slowest, total = max(slowest, elapsed), total+elapsed
        if type(n) is not int or not 0 <= n <= 10**9:
            problems.append(f'turn {turn}: choose_scan returned {n!r}; the server needs an integer from 0')
            n = 0
        cost = 0 if n == 0 else -(-int(n**1.5*1000)//1000)
        radius = min(5*n, 40)
        if cost <= energy:
            energy -= cost
        else:
            radius = 0
        start = time.perf_counter()
        action = strategy.choose_move(observation(rng, turn, position, energy, radius))
        elapsed = time.perf_counter()-start
        slowest, total = max(slowest, elapsed), total+elapsed
        if not isinstance(action, dict) or set(action) != {'direction', 'distance'}:
            problems.append(f'turn {turn}: choose_move must return exactly direction and distance, got {action!r}')
            continue
        direction, distance = action['direction'], action['distance']
        if direction not in DIRECTIONS:
            problems.append(f'turn {turn}: direction {direction!r} is not one of {", ".join(DIRECTIONS)}')
            continue
        if type(distance) is not int or distance < 0:
            problems.append(f'turn {turn}: distance {distance!r} must be an integer from 0')
            continue
        if direction == 'WAIT' and distance:
            problems.append(f'turn {turn}: WAIT requires distance 0, got {distance}')
            continue
        if distance*distance > energy:
            problems.append(f'turn {turn}: {direction} {distance} costs {distance*distance} '
                            f'with {energy} energy; the server would make this WAIT')
            continue
        energy -= distance*distance
        step = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0), 'WAIT': (0, 0)}[direction]
        position = (min(WIDTH-2, max(1, position[0]+step[0]*distance)),
                    min(HEIGHT-2, max(1, position[1]+step[1]*distance)))
    return problems, slowest, total/max(1, 2*turns)


def main():
    parser = argparse.ArgumentParser(description='Check a strategy without a server.')
    parser.add_argument('strategy', nargs='?', default='my_bot.py', help='Strategy file, optionally FILE:CLASS')
    parser.add_argument('--turns', type=int, default=300)
    parser.add_argument('--deadline-ms', type=int, default=250)
    parser.add_argument('--seed', type=int, default=1)
    args = parser.parse_args()
    try:
        strategy_class = load_strategy(args.strategy)
    except (FileNotFoundError, ValueError) as problem:
        raise SystemExit(str(problem))
    problems, slowest, mean = check(strategy_class, args.turns, args.deadline_ms, args.seed)
    print(f'{args.turns} turns · slowest decision {slowest*1000:.1f} ms · average {mean*1000:.1f} ms')
    if slowest*1000 > args.deadline_ms:
        problems.append(f'a decision took {slowest*1000:.0f} ms, longer than the {args.deadline_ms} ms '
                        'budget; the server would use its default for that phase')
    for problem in problems[:10]:
        print(' -', problem)
    if len(problems) > 10:
        print(f' - and {len(problems)-10} more')
    if problems:
        raise SystemExit(f'{len(problems)} problem(s) found.')
    print('No protocol problems. This says nothing about how well it plays.')


if __name__ == '__main__':
    main()
