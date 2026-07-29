"""Notification back-ends (Telegram + console fallback)."""
from __future__ import annotations

import html
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
                 session: Optional[requests.Session] = None, timeout: int = 20):
        self.token = token
        self.chat_id = chat_id
        self.session = session or requests.Session()
        self.timeout = timeout

    def send(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        resp = self.session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
