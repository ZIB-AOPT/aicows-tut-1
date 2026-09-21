#pragma once
// Customize this file; main.cpp handles authentication and the wire protocol.
#include <nlohmann/json.hpp>
#include <array>
#include <set>
#include <string>
#include <utility>

using Json = nlohmann::json;

class MyBot {
public:
    Json config;
    // Add persistent map, target and energy-planning state here.

    void initialize(const Json& message) {
        config = message.at("config");
    }

    int choose_scan(const Json& turn) {
        // n=1 buys radius 5 for one energy; n=0 skips sensing.
        return turn.at("self").at("energy").get<int>() > 0 ? 1 : 0;
    }

    Json choose_move(const Json& observation) {
        const auto& self = observation.at("self");
        if (self.at("energy").get<int>() == 0) {
            return {{"direction", "WAIT"}, {"distance", 0}};
        }
        const auto [x, y] = position(self);
        std::set<Cell> floor, blocked;
        for (const auto& cell : observation.at("terrain")) {
            if (cell.at("kind") == "floor") floor.insert(position(cell));
        }
        for (const auto& other : observation.at("bots")) blocked.insert(position(other));
        const std::array<std::pair<const char*, Cell>, 4> options = {{
            {"N", {x, y - 1}}, {"E", {x + 1, y}},
            {"S", {x, y + 1}}, {"W", {x - 1, y}}
        }};
        const int shift = (observation.at("turn").get<int>() / 5 + self.at("id").get<int>()) % 4;
        // The same small rotating-walk baseline is used in all three languages.
        for (int offset = 0; offset < 4; ++offset) {
            const auto& [direction, cell] = options[(shift + offset) % 4];
            if (floor.count(cell) && !blocked.count(cell)) {
                return {{"direction", direction}, {"distance", 1}};
            }
        }
        return {{"direction", "WAIT"}, {"distance", 0}};
    }

private:
    using Cell = std::pair<int, int>;
    static Cell position(const Json& value) {
        return {value.at("position").at(0).get<int>(), value.at("position").at(1).get<int>()};
    }
};
