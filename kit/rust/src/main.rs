mod bot;

use bot::MyBot;
use serde_json::{json, Value};
use std::{env, error::Error, io, thread, time::Duration};
use tungstenite::{
    client::{connect_with_config, IntoClientRequest},
    http::header::AUTHORIZATION,
    protocol::WebSocketConfig,
    Message,
};

const PROTOCOL: &str = "hidden-gems-2.0";
const HELP: &str = "Usage: hiddengems-bot [--server URL] [--name NAME] [--match MATCH_ID] [--once]\nWithout --match the server seats this credential in the round it belongs to.\nSet HIDDENGEMS_SERVER to the arena URL and HIDDENGEMS_TOKEN to your credential.";

fn invalid(message: &str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidInput, message)
}

fn run() -> Result<(), Box<dyn Error>> {
    let mut server = env::var("HIDDENGEMS_SERVER")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .map(|value| value.trim().to_owned())
        .unwrap_or_else(|| "http://127.0.0.1:8765".to_owned());
    let mut match_id = String::new();
    let mut name = "Rust template".to_owned();
    let mut once = false;
    let mut args = env::args().skip(1);
    while let Some(option) = args.next() {
        if option == "--help" || option == "-h" {
            println!("{HELP}");
            return Ok(());
        }
        if option == "--once" {
            once = true;
            continue;
        }
        if !["--server", "--match", "--name"].contains(&option.as_str()) {
            return Err(invalid("Unknown argument; use --help").into());
        }
        let value = args.next().ok_or_else(|| invalid("Missing option value"))?;
        match option.as_str() {
            "--server" => server = value,
            "--match" => match_id = value,
            "--name" => name = value,
            _ => unreachable!(),
        }
    }
    // Without a match ID the server seats this credential in the round it
    // belongs to, which is how an event with a roster is played.
    let target = if match_id.is_empty() {
        "current".to_owned()
    } else if match_id.len() == 16 && match_id.bytes().all(|b| b.is_ascii_hexdigit()) {
        match_id.clone()
    } else {
        return Err(
            invalid("--match must be the server's 16-character hexadecimal match ID").into(),
        );
    };
    let token = env::var("HIDDENGEMS_TOKEN")
        .or_else(|_| env::var("HIDDENGEMS_BOT_TOKEN"))
        .map_err(|_| invalid("Set HIDDENGEMS_TOKEN to your credential"))?;
    let token = token.trim().to_owned();
    if token.is_empty() {
        return Err(invalid("HIDDENGEMS_TOKEN cannot be empty").into());
    }
    let base = server.trim_end_matches('/');
    let (scheme, authority) = base
        .split_once("://")
        .ok_or_else(|| invalid("Server URL requires a scheme"))?;
    let ws_scheme = match scheme {
        "http" | "ws" => "ws",
        "https" | "wss" => "wss",
        _ => return Err(invalid("Use an http, https, ws or wss server URL").into()),
    };
    if authority.is_empty() || authority.contains(['/', '?', '#', '@']) {
        return Err(
            invalid("Use a server origin without a path, query or embedded credentials").into(),
        );
    }
    let url = format!("{ws_scheme}://{authority}/ws/bot/{target}");
    // An explicit match is one game and does not wait; a seated credential waits
    // for its round, and keeps playing them unless --once was asked for.
    let single = !match_id.is_empty();
    loop {
        match play(&url, &token, &name) {
            Ok(()) => {
                if single || once {
                    return Ok(());
                }
            }
            Err(error) => {
                if single {
                    return Err(error);
                }
                if let Some(tungstenite::Error::Http(response)) =
                    error.downcast_ref::<tungstenite::Error>()
                {
                    // Credentials will not become valid by asking again.
                    if response.status() == 401 || response.status() == 403 {
                        return Err(error);
                    }
                }
                eprintln!("Waiting for a round to open ({error})");
            }
        }
        thread::sleep(Duration::from_secs(2));
    }
}

fn play(url: &str, token: &str, name: &str) -> Result<(), Box<dyn Error>> {
    let mut request = url.into_client_request()?;
    request
        .headers_mut()
        .insert(AUTHORIZATION, format!("Bearer {token}").parse()?);
    // Do not forward slot credentials through HTTP redirects. TLS verifies both
    // the certificate chain and the server name using the platform trust roots.
    let config = WebSocketConfig::default().max_message_size(Some(1 << 20));
    let (mut socket, _) = connect_with_config(request, Some(config), 0)?;
    socket.send(Message::Text(
        json!({"type": "hello", "protocol": PROTOCOL, "name": name})
            .to_string()
            .into(),
    ))?;
    let mut bot = MyBot::default();
    let mut initialized = false;
    loop {
        match socket.read()? {
            Message::Text(text) => {
                let message: Value = serde_json::from_str(&text)?;
                let kind = message["type"]
                    .as_str()
                    .ok_or_else(|| invalid("Message has no type"))?;
                if !initialized && kind != "init" {
                    return Err(invalid("Expected init before game messages").into());
                }
                let reply = match kind {
                    "init" => {
                        if initialized || message["protocol"] != PROTOCOL {
                            return Err(invalid("Unexpected init or incompatible protocol").into());
                        }
                        bot.initialize(&message);
                        initialized = true;
                        eprintln!("Connected. Waiting for the operator to start the match.");
                        None
                    }
                    "turn" => Some(
                        json!({"type": "scan", "turn": message["turn"], "n": bot.choose_scan(&message)}),
                    ),
                    "observation" => {
                        let action = bot.choose_move(&message);
                        Some(json!({"type": "move", "turn": message["turn"],
                                    "direction": action["direction"], "distance": action["distance"]}))
                    }
                    "result" => {
                        println!("{message}");
                        let _ = socket.close(None);
                        return Ok(());
                    }
                    _ => return Err(invalid("Unknown game message type").into()),
                };
                if let Some(reply) = reply {
                    socket.send(Message::Text(reply.to_string().into()))?;
                }
            }
            Message::Ping(_) => socket.flush()?, // Flush tungstenite's automatic pong.
            Message::Close(_) => {
                return Err(invalid("Connection closed before a final result").into())
            }
            Message::Binary(_) => return Err(invalid("Expected text JSON, not binary data").into()),
            _ => {}
        }
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("Bot error: {error}");
        std::process::exit(1);
    }
}
