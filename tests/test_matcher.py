from hn_radar.matcher import InterestMatcher
from conftest import make_story


def test_matches_keyword_case_insensitive():
    m = InterestMatcher(["Rust"])
    assert m.match(make_story(title="A new RUST web framework")) == ["Rust"]


def test_word_boundary_prevents_false_positive():
    m = InterestMatcher(["go"])
    assert m.match(make_story(title="Google releases something")) == []
    assert m.match(make_story(title="Learning Go in 2025")) == ["go"]


def test_phrase_with_hyphen():
    m = InterestMatcher(["local-first"])
    assert m.match(make_story(title="Building local-first software")) == ["local-first"]


def test_matches_in_url_field():
    m = InterestMatcher(["postgres"])
    assert m.match(make_story(title="Cool DB", url="https://postgres.org/x")) == ["postgres"]


def test_multiple_interests_returned():
    m = InterestMatcher(["rust", "wasm"])
    matched = m.match(make_story(title="Rust compiled to wasm"))
    assert set(matched) == {"rust", "wasm"}


def test_no_match():
    m = InterestMatcher(["kubernetes"])
    assert m.match(make_story(title="A poem about cats")) == []


def test_blank_interests_ignored():
    m = InterestMatcher(["", "  ", "rust"])
    assert len(m.patterns) == 1
