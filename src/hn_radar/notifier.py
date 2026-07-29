"""Notification back-ends (Telegram + console fallback)."""
from __future__ import annotations

import html
import time
from typing import Optional

import requests

from .hn import Story


def format_new(story: Story, matched) -> str:
    interests = ", ".join(matched)
    title = html.escape(story.title)
    return (
        f"\U0001F195 <b>New {story.section}</b> matching <i>{html.escape(interests)}</i>\n"
        f'<a href="{story.hn_url}">{title}</a>\n'
        f"{story.points} points \u00b7 {story.num_comments} comments \u00b7 by {html.escape(story.author)}"
    )


def format_points(story: Story, matched, threshold: int) -> str:
    title = html.escape(story.title)
    suffix = ""
    if matched:
        suffix = f"\nmatched: <i>{html.escape(', '.join(matched))}</i>"
    return (
        f"\U0001F525 <b>{story.section} reached {story.points} points</b> (\u2265{threshold})\n"
        f'<a href="{story.hn_url}">{title}</a>\n'
        f"{story.num_comments} comments \u00b7 by {html.escape(story.author)}{suffix}"
    )


def format_combined(story: Story, matched, threshold: int) -> str:
    interests = ", ".join(matched)
    title = html.escape(story.title)
    return (
        f"\U0001F195\U0001F525 <b>New {story.section}</b> matching <i>{html.escape(interests)}</i>"
        f" \u2014 already at {story.points} points (\u2265{threshold})\n"
        f'<a href="{story.hn_url}">{title}</a>\n'
        f"{story.points} points \u00b7 {story.num_comments} comments \u00b7 by {html.escape(story.author)}"
    )


class ConsoleNotifier:
    """Prints messages to stdout. Used for local dry-runs."""

    def send(self, text: str) -> None:
        print("-" * 60)
        print(text)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str,
                 session: Optional[requests.Session] = None, timeout: int = 20,
                 min_interval: float = 1.0, max_retries: int = 5):
        self.token = token
        self.chat_id = chat_id
        self.session = session or requests.Session()
        self.timeout = timeout
        self.min_interval = min_interval
        self.max_retries = max(1, max_retries)
        self._last_send = 0.0

    def _pace(self) -> None:
        """Keep at most one message per ``min_interval`` seconds (Telegram
        recommends <= 1 msg/sec to a single chat)."""
        if self.min_interval > 0:
            elapsed = time.monotonic() - self._last_send
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self._last_send = time.monotonic()

    @staticmethod
    def _retry_after(resp: requests.Response) -> float:
        try:
            retry = resp.json().get("parameters", {}).get("retry_after")
            if retry is not None:
                return float(retry) + 0.5
        except ValueError:
            pass
        return 2.0

    def send(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        resp = None
        for _ in range(self.max_retries):
            self._pace()
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 429:
                time.sleep(self._retry_after(resp))
                continue
            resp.raise_for_status()
            return
        # Retries exhausted on 429 (or persistent errors): surface the last one.
        if resp is not None:
            resp.raise_for_status()

