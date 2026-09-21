# Rust bot

Requires a current Rust toolchain with Cargo. From the repository root:

```sh
cargo build --release --locked --manifest-path examples/rust/Cargo.toml
export HIDDENGEMS_BOT_TOKEN='your-slot-token'
examples/rust/target/release/hiddengems-bot --match MATCH_ID --name 'My Rust bot'
```

Add `--server https://your-server.example` for a remote server. Edit `MyBot` in
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
cargo fmt --check --manifest-path examples/rust/Cargo.toml
cargo clippy --release --locked --manifest-path examples/rust/Cargo.toml -- -D warnings
```
