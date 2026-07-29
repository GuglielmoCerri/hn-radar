"""Configuration loaded entirely from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Mapping, Optional

DEFAULT_SECTIONS = ["story", "show_hn", "ask_hn"]
DEFAULT_MATCH_FIELDS = ["title", "url", "story_text"]

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def _split(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _env_int(value: Optional[str], default: int) -> int:
    if value is None or str(value).strip() == "":
        return default
    return int(value)


def _env_float(value: Optional[str], default: float) -> float:
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def _env_bool(value: Optional[str], default: bool) -> bool:
    if value is None or str(value).strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


@dataclass
class Config:
    interests: List[str] = field(default_factory=list)
    points_threshold: int = 100
    sections: List[str] = field(default_factory=lambda: list(DEFAULT_SECTIONS))
    lookback_hours: int = 48
    hits_per_page: int = 200
    state_cap: int = 5000
    match_fields: List[str] = field(default_factory=lambda: list(DEFAULT_MATCH_FIELDS))
    alert_new_matching: bool = True
    alert_points_threshold: bool = True
    points_require_interest: bool = False
    max_alerts_per_run: int = 25
    send_interval: float = 1.0

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "Config":
        """Build configuration purely from environment variables.

        Recognised variables (all optional except interests, which drives
        interest matching):

        - HN_RADAR_INTERESTS            comma-separated keywords/phrases
        - HN_RADAR_POINTS_THRESHOLD     integer, default 100
        - HN_RADAR_SECTIONS             comma-separated, default story,show_hn,ask_hn
        - HN_RADAR_MATCH_FIELDS         comma-separated, default title,url,story_text
        - HN_RADAR_LOOKBACK_HOURS       integer, default 48
        - HN_RADAR_HITS_PER_PAGE        integer, default 200
        - HN_RADAR_STATE_CAP            integer, default 5000
        - HN_RADAR_ALERT_NEW_MATCHING   bool, default true
        - HN_RADAR_ALERT_POINTS         bool, default true
        - HN_RADAR_POINTS_REQUIRE_INTEREST  bool, default false
        - HN_RADAR_MAX_ALERTS_PER_RUN   integer, default 25 (0 = unlimited)
        - HN_RADAR_SEND_INTERVAL        float seconds between sends, default 1.0
        """
        env = os.environ if env is None else env

        return cls(
            interests=_split(env.get("HN_RADAR_INTERESTS")),
            points_threshold=_env_int(env.get("HN_RADAR_POINTS_THRESHOLD"), 100),
            sections=_split(env.get("HN_RADAR_SECTIONS")) or list(DEFAULT_SECTIONS),
            lookback_hours=_env_int(env.get("HN_RADAR_LOOKBACK_HOURS"), 48),
            hits_per_page=_env_int(env.get("HN_RADAR_HITS_PER_PAGE"), 200),
            state_cap=_env_int(env.get("HN_RADAR_STATE_CAP"), 5000),
            match_fields=_split(env.get("HN_RADAR_MATCH_FIELDS")) or list(DEFAULT_MATCH_FIELDS),
            alert_new_matching=_env_bool(env.get("HN_RADAR_ALERT_NEW_MATCHING"), True),
            alert_points_threshold=_env_bool(env.get("HN_RADAR_ALERT_POINTS"), True),
            points_require_interest=_env_bool(env.get("HN_RADAR_POINTS_REQUIRE_INTEREST"), False),
            max_alerts_per_run=_env_int(env.get("HN_RADAR_MAX_ALERTS_PER_RUN"), 25),
            send_interval=_env_float(env.get("HN_RADAR_SEND_INTERVAL"), 1.0),
        )
