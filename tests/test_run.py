import time

from hn_radar.config import Config
from hn_radar.state import State
from hn_radar.notifier import ConsoleNotifier
from hn_radar.main import run
from conftest import make_story


class FakeClient:
    """Returns canned stories regardless of query."""

    def __init__(self, stories):
        self.stories = stories

    def search(self, section, numeric_filters=None, by_date=False, hits_per_page=200):
        return list(self.stories)


class RecordingNotifier(ConsoleNotifier):
    def __init__(self):
        self.messages = []

    def send(self, text):
        self.messages.append(text)


def base_config(**kw):
    params = dict(interests=["rust"], points_threshold=100, sections=["story"])
    params.update(kw)
    return Config(**params)


def test_new_matching_alert_fires_once(tmp_path):
    now = int(time.time())
    story = make_story(id="1", title="Rust is great", points=5, created_at_i=now)
    client = FakeClient([story])
    state = State.load(str(tmp_path / "s.json"))
    notifier = RecordingNotifier()

    new, points, combined = run(base_config(), client, notifier, state, now=now)
    assert len(new) == 1 and len(points) == 0 and len(combined) == 0

    # Second run: already notified -> no new alerts.
    new2, _, _ = run(base_config(), client, notifier, state, now=now)
    assert new2 == []


def test_points_alert_for_any_hot_post_by_default(tmp_path):
    now = int(time.time())
    hot_unmatched = make_story(id="2", title="Cats on the moon", points=250, created_at_i=now)
    client = FakeClient([hot_unmatched])
    state = State.load(str(tmp_path / "s.json"))

    # Default points_require_interest is False -> any hot post alerts.
    _, points, _ = run(base_config(), client, RecordingNotifier(), state, now=now)
    assert len(points) == 1


def test_points_alert_suppressed_when_require_interest_enabled(tmp_path):
    now = int(time.time())
    hot_unmatched = make_story(id="2b", title="Cats on the moon", points=250, created_at_i=now)
    client = FakeClient([hot_unmatched])
    state = State.load(str(tmp_path / "s.json"))
    cfg = base_config(points_require_interest=True)

    _, points, _ = run(cfg, client, RecordingNotifier(), state, now=now)
    assert points == []


def test_points_alert_all_when_interest_not_required(tmp_path):
    now = int(time.time())
    hot_unmatched = make_story(id="3", title="Cats on the moon", points=250, created_at_i=now)
    client = FakeClient([hot_unmatched])
    state = State.load(str(tmp_path / "s.json"))
    cfg = base_config(points_require_interest=False)

    _, points, _ = run(cfg, client, RecordingNotifier(), state, now=now)
    assert len(points) == 1


def test_both_triggers_are_combined_into_one_alert(tmp_path):
    now = int(time.time())
    story = make_story(id="4", title="Rust hits 200", points=200, created_at_i=now)
    client = FakeClient([story])
    state = State.load(str(tmp_path / "s.json"))
    notifier = RecordingNotifier()

    new, points, combined = run(base_config(), client, notifier, state, now=now)
    assert len(new) == 0 and len(points) == 0 and len(combined) == 1
    # Exactly one message is sent, not two.
    assert len(notifier.messages) == 1


def test_trending_ping_on_later_run_is_not_suppressed(tmp_path):
    now = int(time.time())
    state = State.load(str(tmp_path / "s.json"))

    # First run: post is new & matches but below threshold -> new alert only.
    cold = make_story(id="6", title="Rust project", points=5, created_at_i=now)
    new, points, combined = run(base_config(), FakeClient([cold]), RecordingNotifier(), state, now=now)
    assert len(new) == 1 and len(points) == 0 and len(combined) == 0

    # Later run: same post crossed the threshold -> points ("trending") alert.
    hot = make_story(id="6", title="Rust project", points=150, created_at_i=now)
    new2, points2, combined2 = run(base_config(), FakeClient([hot]), RecordingNotifier(), state, now=now)
    assert len(new2) == 0 and len(points2) == 1 and len(combined2) == 0
