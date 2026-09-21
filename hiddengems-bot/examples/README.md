# Bot templates

Choose a language, build its client, and customize its strategy hooks:

| Language | Strategy template | Build/run instructions |
|---|---|---|
| Python | [`python/bot.py`](python/bot.py) | [Python guide](python/README.md) |
| Rust | [`rust/src/bot.rs`](rust/src/bot.rs) | [Rust guide](rust/README.md) |
| C++ | [`cpp/src/bot.hpp`](cpp/src/bot.hpp) | [C++ guide](cpp/README.md) |

All three templates implement the current `hidden-gems-2.0` protocol. Their
starting strategy buys a radius-5 scan for one energy, then walks one cell into
observed unoccupied floor, with a rotating direction preference. This small
baseline is deliberately easy to replace. The existing, more capable Python
mapper is preserved as [`python/mapper_bot.py`](python/mapper_bot.py).

## Connect an entrant

1. Start the server and create a match through the operator UI or API.
2. Obtain the match ID and **one bot slot token** from its bot-access download.
3. Set `HIDDENGEMS_BOT_TOKEN` in the bot's environment, then launch that language's
   client with `--match MATCH_ID`. All accept optional `--server` and `--name`.
4. Connect the other entrants and start the match from the operator UI.

The default server is `http://127.0.0.1:8765`. Supply a server origin (scheme,
host and optional port) without a path, query or embedded credentials. HTTP/WS
and HTTPS/WSS connections are supported. Secure connections verify the server's
certificate and hostname. Tokens travel in the Authorization header; they are
not command-line arguments or URL parameters.

Every template has `initialize`, `choose_scan` and `choose_move`. Store map and
target memory on the strategy object. `choose_scan` receives free own state and
chooses n (radius 5n, cost ceil(n^1.5)). `choose_move` receives the paid observation
and chooses direction/distance. Distance d costs d². Respond within the server's
phase deadline; long-running planning belongs outside the response path.

Only paid observations reveal gems, walls and opponents. A visible gem includes
its position and remaining `ttl`; radar sees gems through walls, while terrain
and opponents require line of sight. There are no global gem announcements or
score-to-energy trades. See the [complete protocol](../docs/protocol.md).

On completion each client prints the final result as one JSON line. The client
exits nonzero on a connection/protocol failure before that result. Reconnection
is left to your competition launcher. A bot token is different from an operator
or spectator token.

## Check all three clients

After building both native clients and installing the Python project, run from
the repository root:

```sh
.venv/bin/python tools/check_examples.py
.venv/bin/python tools/check_examples.py --tls
```

The checker validates the unmodified templates. It starts its own temporary server on an unused local port, launches
all three languages as separate processes, and checks a real mixed-language
match, failure handling and its replay. It does not touch a running operator
server. TLS checks require the `openssl` executable and use a temporary local
certificate without modifying system trust. Add `--lobby-seconds 32` to exercise
WebSocket heartbeats while the bots wait for the match to start.
