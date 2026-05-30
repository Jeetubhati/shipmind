# ShipMind — 3-minute demo script

Total target: **2:45** (under the hackathon 3-min cap).
Recording tool: Windows Game Bar (`Win + G` → Record, or `Win + Alt + R`).

## Before you start recording

1. **Pre-warm the data.** Full release check takes ~90 s against
   `withcoral/coral` (500+ PRs). Don't make the audience watch that.
   Open `http://localhost:5000` and click **Run Full Release Check**
   once before recording. Let it finish. Leave the tab open.
2. Make sure the gauge shows a real score and all 5 cards are filled.
3. Open a second window: a clean PowerShell terminal in the project
   directory. Type `coral sql "SELECT schema_name, table_name FROM coral.tables LIMIT 1"` so the cursor history is set up.
4. Resize: terminal on the left half, browser on the right half.
   1920×1080 records cleanly at 60 fps; 2560×1440 also works.
5. Close Slack, email, anything that might notify on screen.
6. Mute system sounds; have your microphone tested.

## [0:00 – 0:20] The problem

*Camera on browser, dashboard scrolled to top, gauge visible.*

> "Before every release, an engineer opens four tabs: GitHub, Linear,
> Sentry, Slack. They piece together whether it's safe to ship. It
> takes about 40 minutes and they still miss things. ShipMind does it
> in one dashboard backed by one SQL query language. Built on Coral
> and Claude."

## [0:20 – 0:45] The Coral foundation

*Switch to the terminal window.*

```powershell
coral sql "SELECT schema_name, table_name FROM coral.tables WHERE schema_name IN ('github','linear','sentry','slack_messages') ORDER BY schema_name, table_name LIMIT 20"
```

> "Coral turns four developer APIs into SQL tables — GitHub, Linear,
> Sentry, and a custom Slack messages source I wrote. ShipMind queries
> all of them at once. Here are the tables it sees."

*Output scrolls. Pause for ~3 s.*

## [0:45 – 1:10] The dashboard, already warm

*Switch to the browser. Scroll to the top.*

> "Here's the dashboard. The score is **74 — Ship with Caution**.
> Claude generated this by looking at the results of all 5 release
> checks at once."

*Move cursor across the 5 card titles — Blockers, Readiness, Risk,
Signals, Velocity.*

> "Each card answers one release question. Each pulls from one or
> two real sources."

## [1:10 – 1:45] The cross-source JOIN (the money moment)

*Click the **Risk Assessment** card to scroll to it. Click **Show SQL**
to expand the SQL panel.*

> "This is the unique thing. This SQL is a **cross-source JOIN** —
> GitHub pull requests on the left, Sentry errors on the right, joined
> on the condition that the error first appeared within seven days of
> the PR merging. If a PR ships and a new error class shows up the
> next day, this query finds it."

*Pause. Point at the JOIN clause.*

> "In normal Python this is thirty lines of pagination and timestamp
> reconciliation. Here it's one SQL statement that runs on every team's
> data."

*Scroll down inside the card to show the results table — real PR
titles next to real error titles.*

> "These are real merged PRs from the Coral repo cross-referenced with
> real errors. The analysis underneath is Claude reading the table and
> telling me what to actually do."

## [1:45 – 2:15] Team signals from Slack

*Click the **Team Signals** card.*

> "ShipMind also pulls what the team is saying about the release in
> Slack — release, deploy, ship, blocker keywords. Here are the
> messages from `#releases`."

*Scroll the table briefly so the audience sees real messages including
"blocker: JWT auth PR is still in review" and "deploy checklist for
v1.0".*

> "And here, Claude reads those messages and notes the JWT auth
> blocker explicitly."

## [2:15 – 2:35] Readiness — Linear vs GitHub

*Click the **Release Readiness** card. Show SQL.*

> "And here's another cross-source join: every Linear ticket left-joined
> with GitHub PRs whose title mentions the ticket ID. If a ticket is
> done in Linear but the PR isn't merged, this lights up. One query,
> two sources."

## [2:35 – 2:50] The bounty source

*Optional — only if you're under time.*

*Open a new browser tab to the PR you opened on `withcoral/coral`.*

> "Also part of this submission: a community source spec for dev.to,
> opened as a PR to the Coral repo. So ShipMind isn't just an agent —
> it adds another source the whole Coral community can use."

## [2:50 – 3:00] Close

*Back to dashboard, gauge in centre frame.*

> "ShipMind. Four tabs and forty minutes, collapsed to one dashboard
> and one cross-source query. Built with Coral and Claude in four days."

*End screen with GitHub URL.*

## After recording

1. Trim head/tail in Photos app (Windows built-in editor) or whatever
   you prefer.
2. Upload to **Loom** (fastest, no transcoding wait) or **YouTube
   Unlisted** (more permanent).
3. Copy the share URL into `docs/submission_checklist.md`.

## Fallback if something breaks mid-recording

- **Coral CLI hangs** → close the terminal, open a fresh one, retry.
- **A dashboard card shows an error** → click the next card and keep
  going; the dashboard handles per-card failures so the rest is fine.
- **Full check button is slow live** → switch to running a single
  card with **Run** — those finish in seconds (signals: 1 s,
  velocity: 3 s, blockers: 2 s).
