"""020 — founding is gated in two repos; this is the only thing stopping
a silent split between worldd and the plugin registry."""

from app import factions

from plugin_linear_ascent import unlocks
from plugin_linear_ascent.engine import social


def test_founding_gate_matches_the_plugin():
    assert factions.FOUND_MIN_LEVEL == social.FOUND_MIN_LEVEL
    assert factions.FOUND_FEE == social.GUILD_FOUND_FEE


def test_founding_gate_matches_the_registry():
    u = unlocks.for_option("found_guild")
    assert u is not None
    assert u.at == factions.FOUND_MIN_LEVEL
    assert str(factions.FOUND_FEE) in u.cost
