import json

from hn_radar.state import State


def test_add_and_query(tmp_path):
    path = tmp_path / "seen.json"
    state = State.load(str(path))
    assert not state.has_new("1")
    state.add_new("1")
    state.add_points("2")
    assert state.has_new("1")
    assert state.has_points("2")
    assert not state.has_points("1")


def test_add_is_idempotent(tmp_path):
    state = State.load(str(tmp_path / "s.json"))
    state.add_new("1")
    state.add_new("1")
    assert state.notified_new == ["1"]


def test_persist_and_reload(tmp_path):
    path = tmp_path / "seen.json"
    state = State.load(str(path))
    state.add_new("1")
    state.add_points("9")
    state.save()

    reloaded = State.load(str(path))
    assert reloaded.has_new("1")
    assert reloaded.has_points("9")


def test_cap_keeps_newest(tmp_path):
    state = State.load(str(tmp_path / "s.json"), cap=3)
    for i in range(10):
        state.add_new(str(i))
    data = state.to_dict()
    assert data["notified_new"] == ["7", "8", "9"]
