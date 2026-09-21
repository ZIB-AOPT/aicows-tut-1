# Decisions and accumulated findings

16 September 2026. Current decisions take precedence over archived proposals.

## Agreed game

- Maps are now 120 × 80 cells. Matches support 1–64 bots, default 50.
- Use Rooms (the four inward-facing buildings), Labyrinth, Exploration and
  Long Walls. All passages are at least two cells wide; walls need only one cell.
- Bots have solid bodies. One stationary body can be bypassed when the route
  is otherwise empty. Two or more bodies can still seal a doorway.
- Zero starting energy, three energy added before each turn, no storage cap.
  A straight integer-distance move costs the square of its declared distance.
  Check every crossed cell; collision stops movement without a refund.
- Replace free sensing with paid scans. Radius 5n costs ceil(n^1.5), so the
  costs for n=1,2,3 are 1,3,6 (the original example's third cost of 5 was not
  the stated formula). A scan result arrives before choosing movement.
- Gem radar sees through walls; terrain and opponents require line of sight.
  Own position and movement feedback remain free. Bots maintain their own maps.
- Gem lifetimes are 60/180/300, disclosed when detected; remaining lifetime
  is the collection score. Generation is detailed in Current Rules.
- **Removed by user decision on 16 September:** score-to-energy trading and
  global gem announcements. Neither is a server option or protocol action.

## What earlier experiments showed

All figures below belong to the older geometry, 50-bot populations and specific
reference strategies. They are not balance measurements for 120 × 80 or 64 bots.

The first sequential mechanics study ran 2,340 matches. It examined blocking,
radar, mapping, energy, rays and pills. See reports 05–07 for the measured
comparisons and the distinction between policy quality and rule quality.

The corridor/energy study ran 3,840 matches. Two-wide paths allow a single bot
to be bypassed; deliberate two-body blocking still reduced collection by about
8–9%. Uncapped, zero-start energy with quadratic moves remained finite within a
match; the longest observed burst was 25 cells. Exposing varied lifetimes added
little advantage to the particular planner tested. These are conditional results.

Paid sensing was evaluated in 720 primary matches plus 240 scan-phase checks.
The tested planner beat a simpler mapper by about 14% overall (about 5% in the
labyrinth and 24% in buildings). Scan timing changed which scan policy won:
radius 15 every six turns won with synchronized phases, while radius 10 every
three turns won when the phases were staggered. Avoid hard-coding an example
bot's scan schedule as a game rule.

The last 1,200-match study tested selling score and broadcasting gem births.
With local sensing, selective buying at one point per energy had an adjusted
9.4% advantage over bankers. Under birth announcements that became an 11%
disadvantage. Public birth news increased the movement planner's advantage over
a simpler mapper from 4.6% to 36.9%, while total collection fell about 4.4%.
Collections were not announced: stale targets mattered. The user subsequently
excluded both additions. The records remain useful evidence about uncertainty,
policy interactions and the limits of judging rules by one reference strategy.

The subsequent four-map catalogue passed 400 geometry checks and one full
1,500-turn compatibility match per family. Long Walls had not received a
comparative balance study. Its new 120 × 80 version requires fresh calibration.

## Design implications

Exploration, route memory, scan timing and energy scheduling are separate skills.
A more elaborate bot can lose if its target-value or competition estimate is
poor. No experiment establishes that all sophisticated strategies beat greed.
Use varied maps, independent hidden seeds and rotated starting assignments.
Keep candidate spawns independent of actions, but acknowledge that occupancy
changes which candidates succeed. Report retained score, captures, timeouts and
blocking, and distinguish simulator results from networked program execution.

The game server controls observations and movement; it does not make arbitrary
submitted code safe to execute on its host. Bots connect as separate clients.
For hosted submissions, use a separate container/sandbox worker service.
Spectator credentials must not be given to competitors because the spectator
view deliberately exposes the whole arena.

## Archive index

The numbered files in `history/` preserve the complete rulebook, original
runner/API proposal, spectator design, radar analysis, experiment plans and
results, and both map diagrams. `evidence/` preserves all five reproducible
archives. `history-manifest.json` records their SHA-256 digests. Current Rules
and the implemented protocol supersede conflicts in these snapshots.

