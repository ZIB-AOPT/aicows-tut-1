# Competition format

This is the implementable tournament format for the current four-map ruleset.
It replaces the earlier mixed-map/Chaos proposal preserved in `history/`.
The server accepts 1–64 entrants. A championship has 12 all-entrant matches:
three rounds each of Rooms, Labyrinth, Exploration and Long Walls, cycling in
that order. Each match lasts 1500 turns; there is no elimination. Every match
uses an independent private 256-bit seed and publishes its commitment before
play. One additional Exploration match is reserved for a first-place tie.

Starts are uniformly shuffled distinct floor cells. Slot assignments rotate:
entrant e uses slot `(e + round_index) % bot_count`, with zero-based indices.
That also rotates positions in the roster, though it does not guarantee equal
geographical starts or equal scoring opportunities. All entrants use the same
server deadline and game settings. Freeze submitted bot versions for the whole
championship and give each bot only its own credentials for each round.

## Scoring and ties

Round score is the sum of remaining lifetimes of collected gems. For a round
with winning score W>0, entrant score S contributes **1000 × S/W** championship
points. An all-zero round contributes zero to everyone and counts as no win.
All scheduled rounds count. The server sums exact rational numbers; displayed
three-decimal values are cosmetic and never used to decide a tie.

Rank by, in this order:

1. Total normalized championship points.
2. Total raw gem score.
3. Number of rounds with a positive winning score, including shared wins.
4. Total number of gems collected.
5. Raw score in the final scheduled round.

If first place remains tied after all five checks, run the reserved Exploration
match with the full field. Among the tied leaders only, higher raw reserve-round
score wins. This round adds no championship points. If tied leaders also earn
equal reserve scores, they share the title. Other exact ties share rank; ID
only orders equal rows for display. Competition ranks have gaps (1,1,3).

## Running the event

The browser's **Create 12-round tournament** creates the schedule and all slot
credentials. Download the private entrant-access manifest. “Open next round”
opens the next waiting/running round; attach entrants, then start it. Refresh
“Show standings” after the round finishes. For demonstrations, use “Add example
bots” on each round. External entrants can use the SDK or any language speaking
the WebSocket protocol. Start a round only after every intended bot is ready.

API creation accepts `bots`, `names`, `rounds_per_map` (1–3, default 3), `turns`,
`phase_timeout_ms` and `turn_interval_ms`. Names must be unique. Round objects
contain `match_id`, `map`, `slots` (entry-index to slot-index), seed commitment,
slot-indexed `bot_tokens` and a separate spectator token. Distribute only
`bot_tokens[slots[entry]]` to that entrant. The manifest is operator-only and
contains access to every bot: never publish it as a spectator standings file.

Each round starts through the ordinary match API. The server permits at most
four running matches and 16 waiting/running matches. A standard tournament
occupies 13 slots initially, including its reserve. Unneeded reserve matches
can be stopped to release a waiting slot. Tournament results survive server
restarts; unfinished matches are marked interrupted and cannot resume.

Only `finished` matches contribute to standings. A bot timeout or disconnection
is an entrant failure: apply the normal WAIT/no-scan rules and retain the match.
An infrastructure failure voids that entire round. Use the round replacement endpoint in the [operations guide](operations.md)
to create a fresh match, retaining the old replay and replacement audit trail. Do not award
points from a partial match. This avoids opportunistic reruns based on scores.

The server orchestrates matches and standings; an event organizer supplies
submission deadlines, eligibility, isolated execution and network access for
entrant programs. It does not execute arbitrary uploads or automatically
provision participant containers. Use separate machines/containers with fixed
resource allocations for a public coding contest.

## Presentation

The spectator canvas shows the entire arena, gem decay, bot colors, live rank,
score and energy. Select a bot to inspect its position, captures and missed
deadlines; switch to its exact last paid scan to explain what it could see.
Hide controls for a clean presentation. Show aggregate standings between rounds.
Replays support scrubbing and playback, and can be verified independently.

Short scenes worth explaining: saving energy for a burst, choosing whether a
scan is worth its cost, seeing a gem through a wall and routing around it,
taking a two-wide detour around a stationary bot, and abandoning a gem whose
remaining lifetime is too short. The viewer currently has a fixed full-map
camera; it has no automated commentator or video export.
