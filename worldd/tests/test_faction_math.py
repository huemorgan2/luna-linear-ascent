"""010: the attendance/prize math — pure functions, no DB."""

from app import factions


def test_base_pct_small_vs_full():
    assert factions.base_pct(1) == 0.15
    assert factions.base_pct(3) == 0.15
    assert factions.base_pct(4) == 0.20
    assert factions.base_pct(9) == 0.20


def test_multiplier_zero_below_half():
    # 2 members × 4 required = 8; 3 attended days < 50%
    assert factions.attendance_multiplier(3, 8) == 0.0
    assert factions.attendance_multiplier(0, 8) == 0.0


def test_multiplier_full_at_required():
    assert factions.attendance_multiplier(8, 8) == 1.0


def test_multiplier_proportional_above():
    # 10/8 = 1.25× — showing up more pays more
    assert factions.attendance_multiplier(10, 8) == 1.25


def test_multiplier_caps_at_seven_fourths():
    # everyone all 7 days: 14/8 = 1.75, and it can never exceed that
    assert factions.attendance_multiplier(14, 8) == 1.75
    assert factions.attendance_multiplier(100, 8) == 1.75


def test_multiplier_exactly_half_pays():
    assert factions.attendance_multiplier(4, 8) == 0.5


def test_required_days_prorates_midweek_join():
    week = 10                     # days 70..76
    assert factions.required_days(0, week) == 4      # long-time member
    assert factions.required_days(70, week) == 4     # joined day 1 of week
    assert factions.required_days(74, week) == 3     # 3 days left
    assert factions.required_days(76, week) == 1     # last day
    assert factions.required_days(80, week) == 0     # joined after (edge)


def test_week_bounds_cover_seven_world_days():
    lo, hi = factions.week_bounds_ts(3)
    assert (hi - lo).days == 7


def test_suggest_targets_scale_with_crew():
    small = factions.suggest_targets(2, 3)
    large = factions.suggest_targets(6, 3)
    assert large["hoard"] == 3 * small["hoard"]
    assert large["cull"] == 3 * small["cull"]
    assert small["hoard"] > 0 and small["climb"] > 0
