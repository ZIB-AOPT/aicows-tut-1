# Rust bot

Requires a current Rust toolchain with Cargo. From the repository root:

```sh
cargo build --release --locked --manifest-path kit/rust/Cargo.toml
export HIDDENGEMS_TOKEN='your-credential'
kit/rust/target/release/hiddengems-bot --server https://gemrush.fun --name 'My Rust bot'
```

No match ID: the server seats your credential in the round it belongs to. The
client waits for a round to open, plays it, and waits for the next one; `--once`
stops after a single round and `--match MATCH_ID` plays one specific match. Edit `MyBot` in
`src/bot.rs`; `src/main.rs` owns argument parsing, authentication, WebSockets and
JSON dispatch. `initialize`, `choose_scan` and `choose_move` receive
`serde_json::Value`. Add persistent map/target fields to `MyBot` as your strategy
grows. The client prints the final result as JSON and returns a nonzero status
on failure before completion.

`Cargo.lock` pins the dependency graph. The first build downloads crates; later
builds can use the Cargo cache. The client uses
[tungstenite](https://docs.rs/tungstenite/0.30.0/tungstenite/client/), serde_json and
rustls with the ring provider. TLS uses platform trust roots, with
`SSL_CERT_FILE` available for a private test CA. HTTP redirects are not followed
with bot credentials.

Useful development checks:

```sh
cargo fmt --check --manifest-path kit/rust/Cargo.toml
cargo clippy --release --locked --manifest-path kit/rust/Cargo.toml -- -D warnings
```
