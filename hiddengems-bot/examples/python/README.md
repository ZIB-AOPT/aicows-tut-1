# Python bot

Requires Python 3.11+ and the installed Hidden Gems project. From the repository
root, use the existing virtual environment or set one up:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
export HIDDENGEMS_BOT_TOKEN='your-slot-token'
.venv/bin/python examples/python/bot.py --match MATCH_ID --name 'My Python bot'
```

Add `--server https://your-server.example` for a remote server. The client waits
for the operator to start the match. Customize `MyBot` in `bot.py`; its state
persists between turns. The shared `hiddengems.sdk.run_bot` handles the network
protocol. Own position/energy are in `message['self']`; paid observations add
`terrain`, `bots` and `gems` lists.

Run the existing mapping example with:

```sh
.venv/bin/python examples/python/mapper_bot.py --match MATCH_ID --name Mapper
```

The mapper remains available to the server's **Add example bots** control.
For a private test CA, the standard `SSL_CERT_FILE` environment setting supplies
trust roots. Certificate verification remains enabled.
