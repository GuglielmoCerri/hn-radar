from hn_radar.notifier import TelegramNotifier


class FakeResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def post(self, url, json=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


def test_retries_on_429_then_succeeds(monkeypatch):
    slept = []
    monkeypatch.setattr("hn_radar.notifier.time.sleep", lambda s: slept.append(s))

    session = FakeSession([
        FakeResponse(429, {"parameters": {"retry_after": 1}}),
        FakeResponse(200),
    ])
    notifier = TelegramNotifier("t", "c", session=session, min_interval=0)
    notifier.send("hi")

    assert session.calls == 2
    # Slept roughly retry_after (+ buffer) between the two attempts.
    assert slept and slept[0] >= 1.0


def test_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr("hn_radar.notifier.time.sleep", lambda s: None)
    session = FakeSession([FakeResponse(429, {"parameters": {"retry_after": 0}})
                           for _ in range(3)])
    notifier = TelegramNotifier("t", "c", session=session, min_interval=0, max_retries=3)

    try:
        notifier.send("hi")
        raised = False
    except RuntimeError:
        raised = True
    assert raised
    assert session.calls == 3
