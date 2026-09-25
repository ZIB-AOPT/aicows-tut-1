"""The bot in kit/my_bot.py answers the protocol without crashing or stalling."""

from pathlib import Path

from hiddengems.sdk import load_strategy
from hiddengems.selfcheck import check

BOT = Path(__file__).resolve().parents[1] / "kit" / "my_bot.py"


def test_my_bot_passes_selfcheck():
    problems, slowest, _mean = check(
        load_strategy(str(BOT)), turns=100, deadline_ms=250, seed=1
    )
    assert problems == []
    assert slowest * 1000 <= 250
