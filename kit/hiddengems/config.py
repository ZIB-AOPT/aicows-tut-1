"""Public, validated game configuration. No hidden state belongs here."""
from dataclasses import asdict, dataclass

MAPS = ("rooms", "labyrinth", "exploration", "long-walls")
RULESET = "hidden-gems-2.0"
WIDTH, HEIGHT, MAX_BOTS = 120, 80, 64


@dataclass(frozen=True)
class GameConfig:
    map: str = "exploration"
    bots: int = 50
    turns: int = 1500
    phase_timeout_ms: int = 250
    turn_interval_ms: int = 100

    def __post_init__(self):
        if self.map not in MAPS:
            raise ValueError("Unknown map family")
        for key, lo, hi in (("bots", 1, 64), ("turns", 1, 10000),
                            ("phase_timeout_ms", 10, 10000), ("turn_interval_ms", 0, 10000)):
            value = getattr(self, key)
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{key} must be an integer from {lo} to {hi}")

    def public(self):
        return {**asdict(self), "ruleset": RULESET, "width": WIDTH, "height": HEIGHT,
                "energy_per_turn": 3, "initial_energy": 0, "energy_capacity": None,
                "gem_lifetimes": [60, 180, 300], "max_gems": 20,
                "first_gem_turn": 10, "gem_interval": 3,
                "scan_radius_step": 5, "scan_cost": "ceil(n^1.5)",
                "movement_cost": "distance^2"}

