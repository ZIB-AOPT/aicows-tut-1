# C++ bot

Requires a C++17 compiler, CMake 3.24+ and OpenSSL development files. CMake uses
installed Boost 1.92+ and nlohmann/json 3.12+ when available; otherwise it fetches
fixed releases into the build directory. Boost's first download is substantial.
No Python runtime is required to run the compiled bot.

From the repository root:

```sh
cmake -S kit/cpp -B kit/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build kit/cpp/build --config Release --parallel 2
export HIDDENGEMS_TOKEN='your-credential'
kit/cpp/build/hiddengems-bot --server https://gemrush.fun --name 'My C++ bot'
```

No match ID: the server seats your credential in the round it belongs to. This
client plays one round per run and exits, so wrap it to follow an event:

```sh
until examples/cpp/build/hiddengems-bot --server https://your-server.example --name 'My C++ bot'; do sleep 2; done
```

Add `--match MATCH_ID` to play one specific match instead.

On Windows with a multi-configuration generator, the executable is normally
`examples/cpp/build/Release/hiddengems-bot.exe`. On macOS, install OpenSSL if
needed (`brew install openssl@3`); if CMake cannot locate it, add
`-DOPENSSL_ROOT_DIR="$(brew --prefix openssl@3)"` when configuring. Debian/Ubuntu
systems typically provide the prerequisites as `build-essential cmake libssl-dev`.

Add `--server https://your-server.example` for a remote server. Edit `MyBot` in
`src/bot.hpp`; `src/main.cpp` owns the transport and protocol. Strategy callbacks
use `nlohmann::json`. Add fields to `MyBot` for memory between turns; use
`observation.at("gems")` to inspect detected positions and remaining lifetimes.

WebSockets use [Boost.Beast](https://www.boost.org/libs/beast/), with OpenSSL
certificate-chain and hostname verification for secure servers. A private test
CA can be supplied through `SSL_CERT_FILE`. The client does not follow HTTP
redirects. It prints the final result as JSON and exits nonzero if the connection
ends before a result. JSON integration follows the
[nlohmann CMake interface](https://json.nlohmann.me/integration/cmake/).
