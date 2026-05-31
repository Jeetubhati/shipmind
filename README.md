# ShipMind — Release Intelligence Agent

> Know before you ship. Powered by Coral + an LLM of your choice (Groq Llama 3.3 70B by default; Anthropic Claude Sonnet 4.6 supported).

ShipMind is a release-readiness agent that joins **GitHub, Linear, Sentry,
and Slack in a single SQL query** to answer the question every engineer
asks before tagging a release:

-  **What errors will block this release?** (Sentry)
-  **Are all planned features actually merged?** (Linear ⋈ GitHub)
-  **What did the last few merges break in production?** (GitHub ⋈ Sentry)
-  **What is the team actually saying about the release?** (Slack)
-  **Are we on track this sprint?** (Linear)

Then it asks an LLM (**Groq's Llama 3.3 70B** by default, or
**Anthropic's Claude Sonnet 4.6** if you'd rather) to look at all of
that and give you one recommendation: **SHIP / SHIP WITH CAUTION /
HOLD** plus a 0–100 score.

Built solo for **Pirates of the Coral-bean** · Track 1 · May 2026.

## Demo

![ShipMind dashboard — score 40, HOLD verdict, all 6 sources connected, Groq Llama 3.3 70B analysis](docs/shipmind_dashboard.png)

Live run against `withcoral/coral`. **Score: 40 / HOLD.** The verdict
cites a JWT auth blocker plus DB-pool exhaustion surfaced from Sentry
— both confirmed by the team in `#releases` Slack. The header pill
("Groq · Llama 3.3 70B") shows the active LLM; swap in
`ANTHROPIC_API_KEY` and the same code talks to Claude instead.

## The Problem

Before every release, an engineer opens four tabs — GitHub, Linear,
Sentry, Slack — and manually correlates: "are the planned features in,
did the last deploy break anything, what is the team worried about?"
That ritual takes ~40 minutes and people still miss things, because the
data lives in four different mental models. **ShipMind collapses it to
one dashboard backed by one SQL query language.**

## Architecture

```
                  ┌──────────────────────┐
  Browser ◀──────▶│ Flask  (web/app.py)  │
                  │  4 routes, no JS deps│
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │  Groq (Llama 3.3 70B) │  ← analysis + score
                  │  or Anthropic Claude  │     (auto-detected;
                  │  agent/analyzer.py    │      stub if neither)
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │   Coral CLI / SQL    │  ← coral sql
                  └──┬─────────┬─────────┘
                     │         │
       ┌─────────────┘         └────────────────┐
       │                                        │
  ┌────▼────┐  ┌──────────┐  ┌─────────┐  ┌────▼────────┐  ┌────────┐
  │ github  │  │ linear   │  │ sentry  │  │ slack +     │  │ devto  │
  │ bundled │  │ bundled  │  │ bundled │  │ slack_msgs* │  │ custom*│
  └─────────┘  └──────────┘  └─────────┘  └─────────────┘  └────────┘

  *  slack_messages: custom source spec we authored because the bundled
     Slack source exposes messages only as a table function — we made
     them queryable with `WHERE channel = …`. See sources/slack_messages/.
  *  devto: custom source spec submitted as a community PR to
     withcoral/coral. See sources/devto/.
```

## The money query

```sql
-- PRs merged + Sentry errors that first appeared within the 7-day window
-- after each merge. One query. Two sources. Zero glue code.
SELECT
  p.title         AS pr_merged,
  p.merged_at,
  p.user__login   AS author,
  s.title         AS error_after_merge,
  s.level         AS severity,
  s.count         AS occurrences
FROM github.pulls p
JOIN sentry.issues s
  ON CAST(s.first_seen AS TIMESTAMP) >= CAST(p.merged_at AS TIMESTAMP)
  AND CAST(s.first_seen AS TIMESTAMP) <= CAST(p.merged_at AS TIMESTAMP) + INTERVAL '7 days'
  AND s.level IN ('fatal', 'error')
WHERE p.owner = 'withcoral'
  AND p.repo  = 'coral'
  AND p.state = 'closed'
  AND p.merged_at IS NOT NULL
ORDER BY p.merged_at DESC, s.level
LIMIT 20;
```

This is the cross-source JOIN that would otherwise take ~30 lines of
Python paginating two APIs and reconciling timestamps. With Coral it's
SQL.

## Release readiness score

ShipMind runs five checks and asks Claude to score them 0–100:

| Check | Sources | Typical latency on our test data |
|---|---|---|
|  Release Blockers | sentry | ~2 s |
|  Feature Readiness | linear ⋈ github.pulls | ~30–60 s (GitHub paginates) |
|  Risk Assessment | github.pulls ⋈ sentry.issues | ~30 s (GitHub paginates) |
|  Team Signals | slack_messages | ~1 s |
|  Sprint Velocity | linear | ~3 s |

Full check totals ~90 s against a 500-PR repo; individual cards run
on demand from the dashboard and stay snappy for everything except
the GitHub-heavy queries.

## Setup

### Prerequisites

- **Coral CLI** ([install](https://withcoral.com)) — `coral --version`
  should print `0.3.0+` or later.
- **Python 3.11+** (3.13 tested).
- Tokens for **GitHub, Linear, Sentry, Slack** — see
  `.env.example` for the exact scopes each one needs.

### Install

```powershell
git clone https://github.com/Jeetubhati/shipmind
cd shipmind
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Connect the bundled sources

```powershell
$env:GITHUB_TOKEN  = "ghp_…"          # repo + workflow scopes
$env:LINEAR_API_KEY = "lin_api_…"
$env:SENTRY_TOKEN  = "sntryu_…"
$env:SENTRY_ORG    = "your-org-slug"
$env:SLACK_TOKEN   = "xoxb-…"

coral source add github
coral source add linear
coral source add sentry
coral source add slack
```

### Install the custom Slack messages source

The bundled Slack source exposes messages only as a table function.
ShipMind ships a thin `slack_messages` source that wraps the same API
into a regular table with a `WHERE channel = …` filter:

```powershell
$env:SLACK_MESSAGES_TOKEN = $env:SLACK_TOKEN
coral source add --file sources\slack_messages\slack_messages.yaml
```

### Configure and run

```powershell
Copy-Item .env.example .env
# Edit .env: set GROQ_API_KEY (free at console.groq.com) or
# ANTHROPIC_API_KEY (console.anthropic.com), plus GITHUB_ORG,
# GITHUB_REPO, SLACK_CHANNEL_ID, etc.
.\venv\Scripts\Activate.ps1
python web\app.py
# Open http://localhost:5000
```

ShipMind auto-detects the LLM provider at startup:
- `GROQ_API_KEY` set → Groq via OpenAI-compatible API (default model: `llama-3.3-70b-versatile`)
- `ANTHROPIC_API_KEY` set → Anthropic (default model: `claude-sonnet-4-6`)
- Neither set → deterministic stub analysis so the dashboard still demos

## Repo layout

```
shipmind/
├── agent/                          # the brain
│   ├── config.py                   # env + CORAL_CONTEXT schema doc
│   ├── coral_runner.py             # `coral sql` subprocess wrapper
│   ├── queries.py                  # 5 release-readiness queries
│   ├── analyzer.py                 # Claude analysis + score
│   └── test_agent.py               # smoke test for all 5 queries
├── web/
│   ├── app.py                      # Flask: /, /api/status, /api/query, /api/check
│   ├── templates/index.html        # full dashboard, no CDN, no framework
│   └── static/style.css            # (unused — all CSS is inline in the template)
├── sources/
│   ├── slack_messages/             # custom source: Slack messages as a table
│   │   └── slack_messages.yaml
│   └── devto/                      # bounty source: dev.to Forem
│       └── devto.yaml
├── tests/queries.sql               # the original cross-source JOIN
├── docs/
│   ├── blog_post.md
│   └── shipmind_dashboard.png
├── .env.example
├── requirements.txt
└── README.md
```

## Judging-criteria self-assessment

| Criterion | ShipMind |
|---|---|
| **Impact** | Every team ships code; the 4-tab pre-release ritual is universal. |
| **Creativity** | Proactive release-gate, not a reactive incident tool. |
| **Technical** | 6 sources (4 bundled + 2 custom-authored), real cross-source JOINs, pluggable LLM layer (Groq or Anthropic) with graceful no-key stub fallback. |
| **Best Use of Coral** | The GitHub ⋈ Sentry time-overlap JOIN is the unique value — impossible without Coral. |
| **Aesthetics** | Dark dashboard, animated score gauge, severity-coloured tables, no external dependencies. |

## Also included

- **dev.to (Forem) community source** — submitted as a PR to
  [`withcoral/coral`](https://github.com/withcoral/coral). See
  `sources/devto/devto.yaml`.
- **`slack_messages` custom source** — gives `slack.messages(…)` a
  regular-table interface. Lives in `sources/slack_messages/`.

## What's next

- **PagerDuty + LaunchDarkly sources** — answer "is there an active
  incident right now?" and "what flags are gating this release?".
- **Webhook digest** — schedule the full check, post the result to a
  Slack channel, and Slack-thread the verdict.
- **Push-down filters** — Coral's GitHub source paginates without
  pushing `WHERE state = 'closed' AND merged_at IS NOT NULL` down, so
  500-PR repos take ~30 s. A source-spec contribution to fix that
  would benefit every Coral user.

---

Built solo for **Pirates of the Coral-bean** | May 2026 | Track 1.
