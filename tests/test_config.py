from hn_radar.config import Config, DEFAULT_SECTIONS, DEFAULT_MATCH_FIELDS


def test_defaults_when_no_env():
    cfg = Config.from_env(env={})
    assert cfg.interests == []
    assert cfg.points_threshold == 100
    assert cfg.sections == DEFAULT_SECTIONS
    assert cfg.match_fields == DEFAULT_MATCH_FIELDS
    assert cfg.alert_new_matching is True
    assert cfg.alert_points_threshold is True
    assert cfg.points_require_interest is False
    assert cfg.max_alerts_per_run == 25
    assert cfg.send_interval == 1.0


def test_parses_interests_and_threshold():
    cfg = Config.from_env(env={
        "HN_RADAR_INTERESTS": "rust, 3D , local-first",
        "HN_RADAR_POINTS_THRESHOLD": "150",
    })
    assert cfg.interests == ["rust", "3D", "local-first"]
    assert cfg.points_threshold == 150


def test_sections_override():
    cfg = Config.from_env(env={"HN_RADAR_SECTIONS": "show_hn,ask_hn"})
    assert cfg.sections == ["show_hn", "ask_hn"]


def test_empty_sections_falls_back_to_default():
    cfg = Config.from_env(env={"HN_RADAR_SECTIONS": "  "})
    assert cfg.sections == DEFAULT_SECTIONS


def test_bool_parsing():
    cfg = Config.from_env(env={"HN_RADAR_POINTS_REQUIRE_INTEREST": "false"})
    assert cfg.points_require_interest is False
    cfg2 = Config.from_env(env={"HN_RADAR_ALERT_POINTS": "0"})
    assert cfg2.alert_points_threshold is False


def test_blank_int_uses_default():
    cfg = Config.from_env(env={"HN_RADAR_POINTS_THRESHOLD": ""})
    assert cfg.points_threshold == 100
