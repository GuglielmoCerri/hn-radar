"""Entry point: fetch candidates, match, de-duplicate, notify, persist state."""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List, Tuple

from .config import Config
from .hn import HNClient, Story
from .matcher import InterestMatcher
from .notifier import (
    ConsoleNotifier,
    TelegramNotifier,
    format_combined,
    format_new,
    format_points,
)
from .state import State


def _gather_candidates(client: HNClient, config: Config, cutoff: int) -> List[Story]:
    stories = {}
    for section in config.sections:
        if config.alert_new_matching:
            for story in client.search(
                section,
                numeric_filters=[f"created_at_i>{cutoff}"],
                by_date=True,
                hits_per_page=config.hits_per_page,
            ):
                stories[story.id] = story
        if config.alert_points_threshold:
            for story in client.search(
                section,
                numeric_filters=[
                    f"points>={config.points_threshold}",
                    f"created_at_i>{cutoff}",
                ],
                by_date=False,
                hits_per_page=config.hits_per_page,
            ):
                # Prefer the freshest points count if we already saw the story.
                stories[story.id] = story
    return list(stories.values())


def run(config: Config, client: HNClient, notifier, state: State, now: int = None) -> Tuple[list, list, list]:
    now = now or int(time.time())
    cutoff = now - config.lookback_hours * 3600
    matcher = InterestMatcher(config.interests, fields=config.match_fields)

    new_alerts = []
    points_alerts = []
    combined_alerts = []

    for story in _gather_candidates(client, config, cutoff):
        matched = matcher.match(story)

        fires_new = (
            config.alert_new_matching and bool(matched) and not state.has_new(story.id)
        )
        fires_points = (
            config.alert_points_threshold
            and story.points >= config.points_threshold
            and not state.has_points(story.id)
            and (not config.points_require_interest or bool(matched))
        )

        if fires_new:
            state.add_new(story.id)
        if fires_points:
            state.add_points(story.id)

        if fires_new and fires_points:
            combined_alerts.append((story, matched))
        else:
            if fires_new:
                new_alerts.append((story, matched))
            if fires_points:
                points_alerts.append((story, matched))

    for story, matched in new_alerts:
        notifier.send(format_new(story, matched))
    for story, matched in points_alerts:
        notifier.send(format_points(story, matched, config.points_threshold))
    for story, matched in combined_alerts:
        notifier.send(format_combined(story, matched, config.points_threshold))

    return new_alerts, points_alerts, combined_alerts


def build_notifier(dry_run: bool):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if dry_run or not (token and chat_id):
        if not dry_run:
            print("[hn-radar] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set; "
                  "falling back to console output.", file=sys.stderr)
        return ConsoleNotifier()
    return TelegramNotifier(token, chat_id)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Alert on new & trending Hacker News posts.")
    parser.add_argument("--state", default="state/seen.json", help="Path to state JSON.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print notifications instead of sending them.")
    args = parser.parse_args(argv)

    config = Config.from_env()
    if not config.interests:
        print("[hn-radar] No interests configured (set HN_RADAR_INTERESTS); "
              "only points-threshold alerts can fire.", file=sys.stderr)

    client = HNClient()
    state = State.load(args.state, cap=config.state_cap)
    notifier = build_notifier(args.dry_run)

    new_alerts, points_alerts, combined_alerts = run(config, client, notifier, state)

    if not args.dry_run:
        state.save()

    print(f"[hn-radar] sent {len(new_alerts)} new-post alert(s), "
          f"{len(points_alerts)} points alert(s), "
          f"{len(combined_alerts)} combined alert(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
