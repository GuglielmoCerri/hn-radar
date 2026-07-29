# hn-radar 📡

Get a **Telegram** message when Hacker News has something you care about, either a
**new post matching your interests** or **any post that
crosses a points threshold**.

Runs entirely on a **scheduled GitHub Action** — no server, no hosting cost. It
remembers what it already sent by committing a small state file back to the repo,
so you're notified about each post at most once.

## How it works

1. A GitHub Action runs on a cron (every 15 min by default).
2. It queries the [Hacker News Algolia API](https://hn.algolia.com/api) for recent
   posts in the sections you watch.
3. Each post is matched against your interest keywords/phrases (case-insensitive,
   word-boundary aware).
4. Two independent triggers can fire:
   - **New matching post**: matches your interests (any score).
   - **Points threshold**: reached `HN_RADAR_POINTS_THRESHOLD` upvotes, default to 100 (optionally
     also required to match your interests).
5. Matching posts are sent to Telegram and recorded in `state/seen.json`.

## Quick start

### 1. Create a Telegram bot and get your token

1. In Telegram, open a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts (choose a name and a username ending in
   `bot`).
3. BotFather replies with a line like:

   ```text
   Use this token to access the HTTP API:
   123456789:AAExampleTokenStringGoesHere
   ```

   That value is your **`TELEGRAM_BOT_TOKEN`**.

### 2. Get your chat id

The bot can only message chats that have messaged it first, so:

1. Open your new bot (BotFather gives you a `t.me/<your_bot>` link) and tap
   **Start**, then send any message (e.g. `hi`).
2. In a browser, open (replace `<YOUR_TOKEN>` with your token):

   ```text
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```

3. In the JSON response, find the `"chat"` object and copy its `"id"`:

   ```json
   "chat": { "id": 123456789, "first_name": "...", "type": "private" }
   ```

   That number is your **`TELEGRAM_CHAT_ID`** (positive for a personal chat,
   negative and starting with `-` for a group).

   > If `"result"` is empty: make sure you sent a message *after* tapping Start,
   > then reload the URL. Alternatively, message [@userinfobot](https://t.me/userinfobot)
   > — it replies with your numeric id directly.

### 3. Configure interests

There is **no config file**, all settings live in the `env:` section of
`.github/workflows/hn-radar.yml`. Edit them directly:

```yaml
      - name: Run hn-radar
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          HN_RADAR_INTERESTS: "rust,postgres,local-first,3D"
          HN_RADAR_POINTS_THRESHOLD: "100"
          HN_RADAR_SECTIONS: "story,show_hn,ask_hn"
        run: uv run hn-radar --state state/seen.json
```

The bot notifies you on **both** reasons: a new post matching `HN_RADAR_INTERESTS`,
and any post crossing `HN_RADAR_POINTS_THRESHOLD`. If you omit `HN_RADAR_SECTIONS`
it defaults to `story,show_hn,ask_hn`, and interest matching searches the default
`match_fields` (title, url, story_text). See the full list under
[Configuration reference](#configuration-reference).

### 4. Add repository secrets

In your GitHub repo → **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
| ------ | ----- |
| `TELEGRAM_BOT_TOKEN` | the token from step 1 |
| `TELEGRAM_CHAT_ID`   | the chat id from step 2 |

Then enable Actions. The workflow (`.github/workflows/hn-radar.yml`) also has a
**Run workflow** button (`workflow_dispatch`) for manual testing.

> The workflow needs `contents: write` permission (already set) so it can commit
> the updated state file.

## Run locally

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.
Install it first (see [installation docs](https://docs.astral.sh/uv/getting-started/installation/)):

- **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows (PowerShell):** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

`uv` creates an isolated virtual environment and installs the package for you, so
you don't need to manage `PYTHONPATH` or activate a venv manually.

```bash
uv sync

# Preview matches without sending to Telegram or touching state:
HN_RADAR_INTERESTS="rust,3D" uv run hn-radar --dry-run

# Real run (sends to Telegram, updates state/seen.json):
export TELEGRAM_BOT_TOKEN=...   TELEGRAM_CHAT_ID=...
export HN_RADAR_INTERESTS="rust,postgres,local-first,3D"
export HN_RADAR_POINTS_THRESHOLD=100
uv run hn-radar
```

> **Setting env vars per shell:** bash/zsh `export X=v` - PowerShell `$env:X="v"` - cmd `set X=v`
>
> `hn-radar` is the console entry point; `uv run python -m hn_radar.main` also works.
> Pass a custom state path with `--state`.

## Configuration reference

All configuration is via environment variables (set them in the workflow's `env:`
section, or in your shell for local runs).

| Env var | Default | Meaning |
| --- | ------- | ------- |
| `HN_RADAR_INTERESTS` | *(empty)* | Comma-separated keywords/phrases to match. |
| `HN_RADAR_POINTS_THRESHOLD` | `100` | Upvotes that trigger a "hot post" alert. |
| `HN_RADAR_SECTIONS` | `story,show_hn,ask_hn` | HN sections to watch. |
| `HN_RADAR_MATCH_FIELDS` | `title,url,story_text` | Where interests are searched. |
| `HN_RADAR_LOOKBACK_HOURS` | `48` | How far back a post counts as recent. |
| `HN_RADAR_ALERT_NEW_MATCHING` | `true` | Enable new-post alerts. |
| `HN_RADAR_ALERT_POINTS` | `true` | Enable points alerts. |
| `HN_RADAR_POINTS_REQUIRE_INTEREST` | `false` | Points alerts must also match interests. |

Booleans accept `true/false`, `1/0`, `yes/no`, `on/off`.

**How the points variables interact:**

| `HN_RADAR_ALERT_POINTS` | `HN_RADAR_POINTS_REQUIRE_INTEREST` | Result |
| --- | --- | --- |
| `true` | `false` *(default)* | Points alert fires for **any** post that reaches the threshold. |
| `true` | `true` | Points alert fires only when a post reaches the threshold **and** matches an interest. |
| `false` | *(any)* | Points trigger is **disabled** — `HN_RADAR_POINTS_REQUIRE_INTEREST` is ignored, no points alerts are sent. |

New-matching-post alerts (`HN_RADAR_ALERT_NEW_MATCHING`) are independent of both.

**Avoiding duplicate pings:** when a post is *both* a new interest match *and* already
over the threshold in the same run, hn-radar sends a single "🆕🔥 New … — already at N
points" message instead of two. If a post you were already alerted about later crosses
the threshold on a **subsequent** run, you still get a "🔥 reached N points" trending
ping — that's a genuine update, not a duplicate.

## Tests

```bash
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE).
