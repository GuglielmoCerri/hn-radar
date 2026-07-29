"""Thin client for the Hacker News Algolia search API.

Docs: https://hn.algolia.com/api
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import requests

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"

# Map friendly section names (used in config) to Algolia tags.
SECTION_TAGS = {
    "story": "story",
    "show_hn": "show_hn",
    "ask_hn": "ask_hn",
}


@dataclass
class Story:
    id: str
    title: str
    url: Optional[str]
    points: int
    num_comments: int
    author: str
    created_at_i: int
    story_text: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_hit(cls, hit: dict) -> "Story":
        return cls(
            id=str(hit.get("objectID")),
            title=hit.get("title") or hit.get("story_title") or "",
            url=hit.get("url"),
            points=hit.get("points") or 0,
            num_comments=hit.get("num_comments") or 0,
            author=hit.get("author") or "",
            created_at_i=hit.get("created_at_i") or 0,
            story_text=hit.get("story_text"),
            tags=list(hit.get("_tags") or []),
        )

    @property
    def hn_url(self) -> str:
        return f"https://news.ycombinator.com/item?id={self.id}"

    @property
    def section(self) -> str:
        if "show_hn" in self.tags:
            return "Show HN"
        if "ask_hn" in self.tags:
            return "Ask HN"
        return "Story"


class HNClient:
    def __init__(self, session: Optional[requests.Session] = None,
                 base_url: str = ALGOLIA_BASE, timeout: int = 20):
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: dict) -> dict:
        resp = self.session.get(f"{self.base_url}/{path}", params=params,
                                timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def search(self, section: str, numeric_filters: Optional[List[str]] = None,
               by_date: bool = False, hits_per_page: int = 200) -> List[Story]:
        """Search a single HN section.

        by_date=True sorts newest-first (best for "new post" detection);
        otherwise Algolia sorts by relevance/popularity.
        """
        tag = SECTION_TAGS.get(section, section)
        path = "search_by_date" if by_date else "search"
        params = {"tags": tag, "hitsPerPage": hits_per_page}
        if numeric_filters:
            params["numericFilters"] = ",".join(numeric_filters)
        data = self._get(path, params)
        return [Story.from_hit(h) for h in data.get("hits", [])]
