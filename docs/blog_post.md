# I built a Release Intelligence Agent in 4 days with Claude Code + Coral (here's the exact route)

> 4 days. 5 cross-source SQL queries. One dashboard that tells you whether to ship. Built solo for Pirates of the Coral-bean.

## The problem every team has but nobody owns

Every engineering team has a release ritual. Before tagging `v1.0`,
someone opens four tabs: GitHub for the merged PRs, Linear for the
planned features, Sentry for the active errors, Slack for "did anyone
mention something blocking?" Then they try to fit it all together in
their head. *Did this PR ship? Did it break anything? Is the team OK
with this going out?*

It takes about forty minutes. People still miss things, because the
correlation isn't in any one tool. The PR landed, the error appeared
six hours later, and unless you specifically time-overlap PR merges
with new error classes you won't see it.

I wanted to build the tool that does that correlation for you, and the
question was: how do you query four totally different APIs in one
operation? The honest answer is "you don't, you write 200 lines of
glue and hope nothing rate-limits." Unless you use **Coral**.

## What Coral actually is

Coral is a local CLI that turns developer APIs into SQL tables. You
run `coral source add github`, hand it a PAT, and now `github.pulls`
is a real table you can `SELECT` from. Same for `linear.issues`,
`sentry.issues`, `slack.channels`. You can JOIN across them. You can
do date arithmetic. You can give the resulting result-set to an LLM as
JSON without writing a single API client.

That last sentence is the whole point. The interesting thing about
Coral isn't "you can query GitHub in SQL" — there are plenty of GraphQL
proxies that do that. The interesting thing is **the JOIN works
across sources.**

```sql
SELECT p.title, s.title AS error
FROM github.pulls p
JOIN sentry.issues s
  ON s.first_seen >= p.merged_at
  AND s.first_seen <= p.merged_at + INTERVAL '7 days'
WHERE p.owner = 'withcoral' AND p.repo = 'coral'
  AND p.state = 'closed' AND p.merged_at IS NOT NULL
ORDER BY p.merged_at DESC LIMIT 20;
```

That's the whole "what did the last few merges break in production"
query. It runs against the live GitHub and Sentry APIs and returns 20
real rows. I'm still a bit dazzled by that.

## Why proactive, not reactive

Most release tools are reactive: a deploy fails, PagerDuty rings, you
roll back. The interesting product is the one that asks *should we even
deploy?* before you press the button. That's a different lens — you're
not assembling an incident timeline, you're assembling a confidence
score for a future event. And confidence comes from correlating signals
across surfaces no one source can see.

ShipMind tries to be that proactive gate. Five questions, each backed
by a real SQL query, then a Claude pass on top to turn the data into a
SHIP / SHIP WITH CAUTION / HOLD recommendation.

## Architecture

```
Browser ─▶ Flask (web/app.py)
              │
              ▼
        Claude Sonnet 4.6  ◀── 5 release questions
              │
              ▼
        Coral CLI (`coral sql ...`)
              │
   ┌─────┬─────┬─────┬──────────────┬───────┐
   ▼     ▼     ▼     ▼              ▼       ▼
 github linear sentry slack    slack_msgs  devto
 bundled bundled bundled bundled  custom    custom
```

- **agent/** holds the brain: a tiny subprocess wrapper around
  `coral sql`, the five release queries, the Claude analyser.
- **web/app.py** is ~80 lines of Flask with four routes.
- **templates/index.html** is the entire dashboard — HTML, CSS, vanilla
  JS, no CDN, no framework. The whole dashboard ships in one file you
  can grep.

That last decision was deliberate. Hackathon dashboards die when you
bring in React + a chart library + Tailwind + a build step. Twenty-four
hours later it's a webpack config problem and not a release problem.

## The key SQL queries

I settled on five questions, each one card on the dashboard.

**Release blockers** — what's actively broken right now:

```sql
SELECT s.title, s.level, s.count, s.first_seen, s.project
FROM sentry.issues s
WHERE s.status = 'unresolved' AND s.level IN ('fatal', 'error')
ORDER BY CASE s.level WHEN 'fatal' THEN 0 WHEN 'error' THEN 1 END,
         s.count DESC
LIMIT 20;
```

**Release readiness** — what's planned vs what's actually merged:

```sql
SELECT l.identifier, l.title, l.state_name, p.number AS pr,
       p.state AS pr_state, p.merged_at
FROM linear.issues l
LEFT JOIN github.pulls p
  ON p.owner = 'withcoral' AND p.repo = 'coral'
  AND lower(p.title) LIKE '%' || lower(l.identifier) || '%'
WHERE l.state_name IN ('In Progress', 'In Review', 'Done', 'Todo')
ORDER BY l.priority, l.state_name LIMIT 25;
```

A `LEFT JOIN` from Linear (truth of planning) into GitHub (truth of
shipping) is exactly the right shape for "are the planned items
actually in?".

**Team signals** — what the team is saying right now:

```sql
SELECT m.text, m.ts, m.user
FROM slack_messages.messages m
WHERE m.channel = 'C0B6VTW5J8G'
  AND (lower(m.text) LIKE '%release%' OR lower(m.text) LIKE '%ship%'
    OR lower(m.text) LIKE '%blocker%' OR lower(m.text) LIKE '%broken%')
ORDER BY m.ts DESC LIMIT 25;
```

I'll come back to why this query needed a custom source spec.

## The cross-source JOIN that made it real

The risk-assessment query is the one that justifies the whole project:

```sql
SELECT p.title AS pr, p.merged_at, p.user__login AS author,
       s.title AS error_after_merge, s.level, s.count
FROM github.pulls p
JOIN sentry.issues s
  ON CAST(s.first_seen AS TIMESTAMP) >= CAST(p.merged_at AS TIMESTAMP)
  AND CAST(s.first_seen AS TIMESTAMP) <=
      CAST(p.merged_at AS TIMESTAMP) + INTERVAL '7 days'
  AND s.level IN ('fatal', 'error')
WHERE p.owner = 'withcoral' AND p.repo = 'coral'
  AND p.state = 'closed' AND p.merged_at IS NOT NULL
  AND CAST(p.merged_at AS TIMESTAMP) >=
      current_timestamp - INTERVAL '30 days'
ORDER BY p.merged_at DESC LIMIT 20;
```

This returned 20 real rows on first run. Every recent PR in the Coral
repo, cross-referenced with the Sentry errors that first appeared in
the seven days after merge. When I saw "PR `feat(sources/community/metabase): add Metabase source` correlated
with `AttributeError: NullReferenceError` first seen 1 day later" I
realised: nothing about that query is GitHub-specific or
Sentry-specific or even ShipMind-specific. **It's a release pattern.
Every team can run it tomorrow.**

## Three things I learned about Coral the hard way

**1. Table functions are not tables.** The bundled Slack source has
`slack.channels` and `slack.users` as plain tables, but messages live
in a *table function* — `slack.messages(channel => 'C0...')`. I
inspected `coral.tables` on day 1, saw no `messages` table, and almost
gave up on Slack. The fix was checking `coral.table_functions` too. The
deeper fix was writing a `slack_messages` source spec myself so I could
say `WHERE channel = 'C0...'` like with any other table.

**2. Column names don't match API docs.** Linear's GraphQL returns
`state.name`; Coral exposes it as `state_name` (single underscore).
GitHub's REST returns `user.login`; Coral exposes it as `user__login`
(double underscore). Sentry's API has a `culprit` field; Coral's
source doesn't expose it. Every query I wrote on day 2 failed on the
first run because I used the API column names. The fix every time was
`SELECT column_name, data_type FROM coral.columns WHERE …` to ground
myself in the real schema. After the third time I added a
`CORAL_CONTEXT` constant in `agent/config.py` listing the canonical
column names for every source.

**3. SQL `LIMIT` isn't pushed down.** When I queried `devto.articles
WHERE username = 'ben' LIMIT 5`, Coral fetched **every** article Ben
has published (3,000+) and then locally took the first 5. That meant
my dev.to source spec's `max_pages: 50` ceiling was insufficient and
the query failed with "exceeded pagination max_pages". The fix was
bumping `per_page` from 30 to 1000 so a typical user's whole feed fits
in one fetch. This is a tradeoff every source author needs to think
about when authoring page-mode pagination.

## Writing the custom sources

I wrote two source specs:

- `sources/slack_messages/` — wraps `conversations.history` so messages
  are a regular table with a `channel` filter. This was for me; it
  makes ShipMind's SQL look uniform across sources.
- `sources/devto/` — three tables (`articles_me`, `articles`, `tags`)
  for the dev.to (Forem) public API. Submitted as a community PR to
  `withcoral/coral`.

Authoring these taught me what a source spec actually is: it's a tiny
YAML file that names a table, points at an HTTP path, declares the
auth, and maps response fields to typed columns. The hardest part isn't
the YAML; it's discovering the field shape. Coral's `lint` is friendly
("dsl_version: 3 was expected") but doesn't tell you the canonical
field names. I ended up reading the source manifest JSON schema
directly and that unlocked everything.

## Building the dashboard

Flask + a single HTML file. Four endpoints:

- `GET /` — renders the dashboard with the source pills
- `GET /api/status` — JSON: are the sources up
- `GET /api/query/<name>` — runs one of the five queries
- `POST /api/check` — runs all five and asks Claude for a score

The HTML uses CSS Grid for the card layout and an inline SVG circle
with `stroke-dasharray` for the score gauge. No CDN. The whole
template is ~640 lines and includes the JavaScript. I can grep it in
one file. I will not give that up for any framework, ever, in a
4-day project.

The analyser falls back to a deterministic stub when there's no
Anthropic API key. So the dashboard demos correctly on a machine
without Claude credentials.

## How to run ShipMind yourself

```bash
git clone https://github.com/Jeetubhati/shipmind
cd shipmind
python -m venv venv
./venv/Scripts/Activate.ps1     # PowerShell; bash uses /bin/activate
pip install -r requirements.txt

# tokens
export GITHUB_TOKEN=ghp_…
export LINEAR_API_KEY=lin_api_…
export SENTRY_TOKEN=sntryu_…   export SENTRY_ORG=your-slug
export SLACK_TOKEN=xoxb-…

coral source add github
coral source add linear
coral source add sentry
coral source add slack
coral source add --file sources/slack_messages/slack_messages.yaml

cp .env.example .env
# edit .env with ANTHROPIC_API_KEY and your channel/team IDs

python web/app.py
# → http://localhost:5000
```

The full README walks through it step by step.

## What's next

- **PagerDuty + LaunchDarkly sources.** ShipMind currently asks
  "what's broken" via Sentry; PagerDuty would tell it "what's *actively
  paging right now*". LaunchDarkly would tell it "what flags gate this
  release". The same proactive-gate frame applies.
- **Webhook digest.** Cron the full check, post the verdict to a Slack
  channel as a thread. Bonus: link each finding back to the source row.
- **A push-down filter contribution.** Coral's GitHub source doesn't
  push `WHERE p.state = 'closed'` down to the API, so we paginate
  every PR for 500-PR repos. Fixing that on the bundled source would
  benefit every Coral user, not just ShipMind.

## Closing thought

The lesson I'll keep from this hackathon is that **the JOIN is the
feature**. I spent the first day worrying about prompts and the
analyser and the dashboard. The thing that actually made the demo land
was discovering that I could ask GitHub and Sentry one question
together — "show me PRs and the errors they caused" — and get an
answer in 30 seconds without writing any client code. Every other
piece of the project is in service of that.

If you build agents that work across tools, Coral is doing something
nobody else does. Try it.

— **Jitendra Bhati** · [github.com/Jeetubhati/shipmind](https://github.com/Jeetubhati/shipmind)
