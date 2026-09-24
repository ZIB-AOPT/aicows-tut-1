# Bot and operator protocol

Protocol identifier: `hidden-gems-2.0`. Messages are UTF-8 JSON objects in text
WebSocket frames. Coordinates are `[x, y]`, zero based from the upper left;
positive x points east, positive y south. All numeric decisions are integers;
JSON booleans are not integers. The server is authoritative.

## Connecting a bot

The operator creates a match and gives each entrant its server URL, match ID and
**one** slot token. Connect to `/ws/bot/{match_id}` with HTTP header
`Authorization: Bearer TOKEN`. A roster participant may connect to
**`/ws/bot/current`** instead and be seated in the round their credential
belongs to, so no match ID is needed at an event; 409 means no round is open
yet and the client should try again shortly. Send this within five seconds:

```json
{"type":"hello","protocol":"hidden-gems-2.0","name":"My mapper"}
```

Names have 1–48 Unicode characters and cannot contain ASCII controls below U+0020.
In a roster match the name of a seat that still carries its roster name is
claimed by the first client that offers one; a name already taken is refused and
the seat keeps its own. The `init` reply carries the effective `name`.
A slot permits one connection. Credentials are never sent in query strings.
The response is `init`, containing `protocol`, `match_id`, public `config`, and
`self`. Public configuration includes map family, dimensions, turn count, timeout
and all cost/gem constants. It contains no wall map or random seed. The initial
energy is zero. Example `self`:

```json
{"id":0,"position":[24,37],"energy":0,"score":0,"captures":0,
 "feedback":{"distance":0,"blocked":false,"reason":null}}
```

## Each turn: scan, observe, move

On turn t the server first expires old gems, attempts the scheduled birth, and
adds three energy to every bot. It sends all bots:

```json
{"type":"turn","turn":0,"self":{"id":0,"position":[24,37],"energy":3,
 "score":0,"captures":0,"feedback":{"distance":0,"blocked":false,"reason":null}},
 "deadline_ms":250}
```

Reply exactly once with `{"type":"scan","turn":0,"n":1}`. Use n=0 to skip.
The cost is the integer ceiling of sqrt(n³); range is Manhattan distance ≤5n.
Radius 15 costs **6**, not 5. Unaffordable scans cost zero and produce an empty
observation with `scan_error: "invalid_or_unaffordable_scan"`.

The server evaluates all scans before moving anyone. It sends:

```json
{"type":"observation","turn":0,"self":{"id":0,"position":[24,37],"energy":2,
 "score":0,"captures":0,"feedback":{"distance":0,"blocked":false,"reason":null}},
 "radius":5,"scan_cost":1,"scan_error":null,
 "terrain":[{"position":[24,37],"kind":"floor"}],
 "bots":[],"gems":[],"deadline_ms":250}
```

The lists above are illustrative; a real scan reports every qualifying cell,
bot and gem. Terrain elements have `position` and `kind` (`floor` or `wall`).
Opponent elements have `id` and `position`, never energy or score. Gem elements
have `id`, `position` and remaining `ttl`. Gem radar ignores intervening walls.
Terrain/opponents use integer Bresenham lines between cell centers: an
intermediate wall blocks the target, but a wall at the target is visible.
Bots do not occlude the view. Range is inclusive. The implementation in
`Engine._visible` fixes the rasterization and corner convention.

Reply with, for example:

```json
{"type":"move","turn":0,"direction":"E","distance":1}
```

Directions: `N`, `E`, `S`, `W`, `WAIT`. WAIT requires distance zero. A zero-length
cardinal move also waits. A straight distance d costs d² using energy remaining
after the scan. Charge the full declared cost before resolving movement; no
refund follows an obstruction. Invalid or unaffordable movement becomes WAIT.
The next free `self.feedback` reports actual distance, `blocked`, and either
null or `invalid_or_unaffordable_move`. It does not reveal the type of a hidden
obstruction. Infer traversed floor from your previous position and direction.

Movement visits cell j at exact fraction j/d. Simultaneous visits are processed
in seeded rotating initiative order against **current** occupancy. Entering a
still-occupied cell stops that burst permanently, even if its occupant moves
later in the turn. Swaps cannot pass through one another. A bot that vacates a
cell earlier at the same fraction can be followed into it by a later-priority
bot. Arrival order resolves gem ownership. All of this is deterministic.

Action messages accept precisely the keys shown above. Integer requests above
1,000,000,000 are rejected by transport validation; they exceed every affordable
request under the supported 10,000-turn maximum and are not a gameplay range
cap. NaN, Infinity, binary messages and extra action fields are not supported.
There is no score trading or gem announcement message.

## Deadlines, failures and completion

Each phase has one concurrent server deadline for all slots, default 250 ms.
The server finishes computing and serializing all observations before starting
that shared clock, so encoding a large scan does not consume decision time.
It includes delivery and network return time; `deadline_ms` is the nominal
budget, not a guarantee of that many milliseconds after receipt. The first
validly shaped response for the current phase/turn is accepted. A malformed
shaped response consumes the decision as a default; malformed JSON is counted
and ignored. Stale, duplicate, out-of-phase and late responses are ignored.

A response for a phase that has already closed is counted **late** rather than
stale: it forfeits its decision like any missing reply, but a link slower than
the deadline is not misbehaviour and must not cost a slot. Duplicate answers to
the open phase, replies for a phase that has not been opened, and malformed
messages remain stale or invalid. A slot is disabled once its invalid and stale
messages exceed 128, or once all three counters together exceed 128 plus twice
the number of phases played, which bounds a client that floods late answers. A
disabled slot is closed with code 1008 and cannot reconnect to that match. The
per-slot counters `timeouts`, `late`, `invalid`, `stale` and `disconnected`
appear in match state, the spectator interface and the replay footer.

Missing scan replies become n=0; missing move replies become WAIT. A disconnected
bot remains a solid, stationary participant and continues gaining energy. It
can reconnect using the same slot token while the match is running; it receives
current own state and can join future phases. No missed decisions are replayed.
The SDK raises an exception if its connection ends before a final result; a
competition launcher should decide its own restart policy.

After the last turn the server sends `{"type":"result","status":"finished",
"self":...}` and closes bot connections. Other terminal statuses are `stopped`,
`interrupted` and `failed`. A stopped match is not a tournament result. A normal
match has decisions numbered 0–1499; `state.turn` is the number of completed
turns, so its final value is 1500. The minimum default wall-clock turn interval
is 100 ms; slow decisions can make a match longer than 150 seconds.
