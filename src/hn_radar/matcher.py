"""Keyword / phrase matching of stories against user interests."""
from __future__ import annotations

import re
from typing import Iterable, List


class InterestMatcher:
    """Match stories against a list of interest keywords or phrases.

    Matching is case-insensitive and word-boundary aware so that an
    interest like "go" won't match "google", while phrases like
    "local-first" are matched literally.
    """

    def __init__(self, interests: Iterable[str], fields: Iterable[str] = ("title", "url", "story_text")):
        self.fields = tuple(fields)
        self.patterns = []
        for interest in interests:
            cleaned = (interest or "").strip()
            if not cleaned:
                continue
            escaped = re.escape(cleaned)
            pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
            self.patterns.append((cleaned, pattern))

    def _text(self, story) -> str:
        parts = []
        for field_name in self.fields:
            value = getattr(story, field_name, None)
            if value:
                parts.append(str(value))
        return " ".join(parts)

    def match(self, story) -> List[str]:
        """Return the list of interests that matched this story."""
        text = self._text(story)
        return [name for name, pattern in self.patterns if pattern.search(text)]
