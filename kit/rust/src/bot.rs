//! Customize this file; main.rs handles authentication and the wire protocol.
use serde_json::{json, Value};
use std::collections::HashSet;

#[derive(Default)]
pub struct MyBot {
    pub config: Value,
    // Add persistent map, target and energy-planning state here.
}

fn position(value: &Value) -> (i64, i64) {
    let p = &value["position"];
    (
        p[0].as_i64().expect("x coordinate"),
        p[1].as_i64().expect("y coordinate"),
    )
}

impl MyBot {
    pub fn initialize(&mut self, message: &Value) {
        self.config = message["config"].clone();
    }

    pub fn choose_scan(&mut self, turn: &Value) -> u64 {
        // n=1 buys radius 5 for one energy; n=0 skips sensing.
        u64::from(turn["self"]["energy"].as_u64().unwrap_or(0) > 0)
    }

    pub fn choose_move(&mut self, observation: &Value) -> Value {
        if observation["self"]["energy"].as_u64().unwrap_or(0) == 0 {
            return json!({"direction": "WAIT", "distance": 0});
        }
        let (x, y) = position(&observation["self"]);
        let floor: HashSet<_> = observation["terrain"]
            .as_array()
            .expect("terrain list")
            .iter()
            .filter(|cell| cell["kind"] == "floor")
            .map(position)
            .collect();
        let blocked: HashSet<_> = observation["bots"]
            .as_array()
            .expect("bot list")
            .iter()
            .map(position)
            .collect();
        let options = [
            ("N", (x, y - 1)),
            ("E", (x + 1, y)),
            ("S", (x, y + 1)),
            ("W", (x - 1, y)),
        ];
        let turn = observation["turn"].as_u64().expect("turn number");
        let id = observation["self"]["id"].as_u64().expect("own ID");
        let shift = ((turn / 5 + id) % 4) as usize;
        // The same small rotating-walk baseline is used in all three languages.
        for offset in 0..4 {
            let (direction, cell) = options[(shift + offset) % 4];
            if floor.contains(&cell) && !blocked.contains(&cell) {
                return json!({"direction": direction, "distance": 1});
            }
        }
        json!({"direction": "WAIT", "distance": 0})
    }
}
