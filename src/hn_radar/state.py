"""Persistent state so we notify about each story at most once per trigger."""
from __future__ import annotations

import json
import os
from typing import Dict, List


class State:
    """Tracks which story IDs have already been notified.

    Two independent buckets are kept because a single story can fire both
    a "new matching post" alert and a "points threshold" alert.
    """

    def __init__(self, path: str, cap: int = 5000):
        self.path = path
        self.cap = cap
        self.notified_new: List[str] = []
        self.notified_points: List[str] = []
        self._new_set = set()
        self._points_set = set()

    @classmethod
    def load(cls, path: str, cap: int = 5000) -> "State":
        state = cls(path, cap=cap)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            state.notified_new = list(data.get("notified_new", []))
            state.notified_points = list(data.get("notified_points", []))
            state._new_set = set(state.notified_new)
            state._points_set = set(state.notified_points)
        return state

    def has_new(self, story_id: str) -> bool:
        return story_id in self._new_set

    def has_points(self, story_id: str) -> bool:
        return story_id in self._points_set

    def add_new(self, story_id: str) -> None:
        if story_id not in self._new_set:
            self._new_set.add(story_id)
            self.notified_new.append(story_id)

    def add_points(self, story_id: str) -> None:
        if story_id not in self._points_set:
            self._points_set.add(story_id)
            self.notified_points.append(story_id)

    def _capped(self, ids: List[str]) -> List[str]:
        return ids[-self.cap:] if self.cap and len(ids) > self.cap else ids

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "notified_new": self._capped(self.notified_new),
            "notified_points": self._capped(self.notified_points),
        }

    def save(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
            fh.write("\n")
