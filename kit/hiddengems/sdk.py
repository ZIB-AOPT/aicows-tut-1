"""Small asynchronous bot client. Strategies see only their allowed messages."""

import asyncio
import json
import math
import random
from collections import deque

from aiohttp import ClientError, ClientSession, WSMsgType

from .config import RULESET


class BotStrategy:
    def initialize(self, message):
        self.config = message["config"]

    def choose_scan(self, turn) -> int:
        return 0

    def choose_move(self, observation):
        return {"direction": "WAIT", "distance": 0}


class MappingBot(BotStrategy):
    """Example mapper, intentionally small enough to replace with a competitor."""

    def initialize(self, message):
        super().initialize(message)
        self.known, self.gems, self.visits = {}, {}, {}
        self.random = random.Random(message["self"]["id"] + 104729)
        self.phase = message["self"]["id"] % 3

    def choose_scan(self, turn):
        return (
            2 if turn["turn"] % 3 == self.phase and turn["self"]["energy"] >= 3 else 0
        )

    @staticmethod
    def neighbors(p):
        x, y = p
        return [
            ("N", (x, y - 1)),
            ("E", (x + 1, y)),
            ("S", (x, y + 1)),
            ("W", (x - 1, y)),
        ]

    def choose_move(self, observation):
        o = observation
        start = tuple(o["self"]["position"])
        self.known[start] = True
        self.visits[start] = self.visits.get(start, 0) + 1
        for cell in o["terrain"]:
            self.known[tuple(cell["position"])] = cell["kind"] == "floor"
        visible_ids = {g["id"] for g in o["gems"]}
        for gid, (p, expiry) in list(self.gems.items()):
            if (
                expiry <= o["turn"]
                or p == start
                or (
                    o["radius"]
                    and abs(p[0] - start[0]) + abs(p[1] - start[1]) <= o["radius"]
                    and gid not in visible_ids
                )
            ):
                del self.gems[gid]
        for gem in o["gems"]:
            self.gems[gem["id"]] = (tuple(gem["position"]), o["turn"] + gem["ttl"])
        occupied = {tuple(b["position"]) for b in o["bots"]}
        parent: dict[tuple, tuple | None] = {start: None}
        distance, queue = {start: 0}, deque([start])
        while queue and len(parent) < 2000:
            p = queue.popleft()
            for direction, q in self.neighbors(p):
                if self.known.get(q) and q not in occupied and q not in parent:
                    parent[q], distance[q] = (p, direction), distance[p] + 1
                    queue.append(q)
        goals = [
            (max(0, expiry - o["turn"] - distance[p]) / (distance[p] + 3), p)
            for p, expiry in self.gems.values()
            if p in parent and p != start
        ]
        target = max(goals, default=(0, None))[1]
        if target is None:
            frontiers = [
                p
                for p in parent
                if p != start and any(q not in self.known for _, q in self.neighbors(p))
            ]
            if frontiers:
                target = min(
                    frontiers, key=lambda p: distance[p] + 3 * self.visits.get(p, 0)
                )
        if target:
            directions = []
            p = target
            while p != start:
                step = parent[p]
                if step is None:
                    break
                p, direction = step
                directions.append(direction)
            directions.reverse()
            maximum = min(2, math.isqrt(o["self"]["energy"]))
            length = 0
            for direction in directions:
                if length == maximum or direction != directions[0]:
                    break
                length += 1
            return {
                "direction": directions[0] if length else "WAIT",
                "distance": length,
            }
        options = [
            (self.visits.get(q, 0) + self.random.random(), direction)
            for direction, q in self.neighbors(start)
            if q not in occupied
            and self.known.get(q, True)
            and 0 < q[0] < self.config["width"] - 1
            and 0 < q[1] < self.config["height"] - 1
        ]
        direction = min(options)[1] if options and o["self"]["energy"] else "WAIT"
        return {"direction": direction, "distance": int(direction != "WAIT")}


class Refused(ValueError):
    """The server answered, and the answer will not change by asking again:
    a wrong token, a server with no roster, or a name already in use. Retrying
    would hide the problem behind a client that looks like it is waiting."""


def load_strategy(reference):
    """Import PATH[:CLASS] and return the strategy class, so every match starts
    from a clean instance of the participant's own file."""
    import importlib.util
    import inspect
    import sys
    from pathlib import Path

    path, _, wanted = reference.partition(":")
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No strategy file at {path}")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import a strategy from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if wanted:
        return getattr(module, wanted)
    classes = [
        value
        for value in vars(module).values()
        if inspect.isclass(value)
        and issubclass(value, BotStrategy)
        and value.__module__ == spec.name
    ]
    if len(classes) != 1:
        raise ValueError(f"Name the class to use, for example {path.name}:MyBot")
    return classes[0]


class NameRefused(Refused):
    """The chosen display name is already in use, or is not a usable name."""


async def explain(response):
    body = (await response.text()).strip()
    try:
        body = json.loads(body).get("error", body)
    except ValueError:
        pass
    return f"HTTP {response.status}: {body or response.reason}"


async def claim_name(session, server, token, name):
    """Choose how the arena and the standings show this participant."""
    async with session.post(
        server.rstrip("/") + "/api/lobby/name",
        json={"name": name},
        headers={"Authorization": "Bearer " + token},
    ) as response:
        if 400 <= response.status < 500:
            raise NameRefused(await explain(response))
        response.raise_for_status()
        return (await response.json())["name"]


async def next_round(session, server, token):
    """Ask the lobby which roster match this participant should join next."""
    async with session.get(
        server.rstrip("/") + "/api/lobby", headers={"Authorization": "Bearer " + token}
    ) as response:
        if 400 <= response.status < 500:
            raise Refused(await explain(response))
        response.raise_for_status()
        return await response.json()


async def run_workshop(
    server,
    token,
    strategy_factory=None,
    name=None,
    poll=2.0,
    once=False,
    announce=None,
    session=None,
):
    """Play every round this participant is seated in, without being told match IDs.

    The strategy factory is called once per match, so each round starts from a
    clean strategy. Connection trouble is retried: a workshop client is expected
    to outlive a flaky network and a server restart.
    """
    strategy_factory = strategy_factory or MappingBot
    announce = announce or (lambda message: None)

    async def loop(client):
        played, idle, trouble = set(), False, 0
        if name:
            announce("Playing as " + await claim_name(client, server, token, name))
        while True:
            try:
                assignment = await next_round(client, server, token)
            except (ClientError, OSError) as error:
                announce(f"Waiting for the server ({type(error).__name__})")
                await asyncio.sleep(poll)
                continue
            match_id = assignment["match_id"]
            if match_id is None or match_id in played:
                if not idle:
                    announce("Waiting for the next round to open")
                    idle = True
                await asyncio.sleep(poll)
                continue
            idle = False
            announce(
                f"Joining {assignment['map']} match {match_id} as "
                f"{assignment['name']} in slot {assignment['slot']}"
                + (
                    ", waiting for the operator to start it"
                    if assignment["status"] == "waiting"
                    else ""
                )
            )
            try:
                result = await run_bot(
                    server,
                    match_id,
                    token,
                    strategy_factory(),
                    name=assignment["name"],
                    session=client,
                )
            except (ClientError, ConnectionError, OSError) as error:
                # A seat can be reclaimed while its match is still running, so a
                # dropped connection must not retire the match this client is in;
                # otherwise one network hiccup benches a participant for the round.
                trouble += 1
                announce(f"Lost match {match_id} ({error}); rejoining")
                await asyncio.sleep(min(poll * 2**trouble, 10))
                continue
            trouble = 0
            announce(json.dumps(result))
            played.add(match_id)
            if once:
                return result

    if session is not None:
        return await loop(session)
    async with ClientSession() as client:
        return await loop(client)


async def run_bot(
    server,
    match_id,
    token,
    strategy=None,
    name="Example mapper",
    ready=None,
    session=None,
):
    strategy = strategy or MappingBot()

    async def play(client):
        async with client.ws_connect(
            server.rstrip("/") + "/ws/bot/" + match_id,
            headers={"Authorization": "Bearer " + token},
            max_msg_size=2**20,
            heartbeat=20,
        ) as ws:
            await ws.send_json({"type": "hello", "protocol": RULESET, "name": name})
            init = await ws.receive_json()
            if init.get("type") != "init":
                raise ValueError("Server did not initialize the bot")
            strategy.initialize(init)
            if ready:
                ready.set()
            async for message in ws:
                if message.type != WSMsgType.TEXT:
                    continue
                value = message.json()
                if value["type"] == "turn":
                    n = strategy.choose_scan(value)
                    await ws.send_json({"type": "scan", "turn": value["turn"], "n": n})
                elif value["type"] == "observation":
                    action = strategy.choose_move(value)
                    await ws.send_json(
                        {"type": "move", "turn": value["turn"], **action}
                    )
                elif value["type"] == "result":
                    return value
            raise ConnectionError("Connection ended before a result")

    if session is not None:
        return await play(session)
    async with ClientSession() as client:
        return await play(client)
