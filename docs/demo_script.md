# ShipMind — 3-minute demo script

Total target: **2:45** (under the hackathon 3-min cap).
Recording tool: Windows Game Bar (`Win + G` → Record, or `Win + Alt + R`).

ShipMind's LLM layer is pluggable: it auto-detects **Groq (Llama 3.3
70B)** or **Anthropic (Claude Sonnet 4.6)** at startup. The default
demo runs on **Groq** because it's fast (~1 s per analysis) and free.

## Before you start recording

1. **Pre-warm the data.** Full release check takes ~90 s against
   `withcoral/coral` (500+ PRs). Don't make the audience watch that.
   Open `http://localhost:5000` and click **Run Full Release Check**
   once before recording. Let it finish. Leave the tab open.
2. The gauge should show a real score and all 5 cards should have
   filled analyses from Llama 3.3 70B (you'll see the "Groq · Llama
   3.3 70B" pill in the header — that's the visual proof the LLM is
   live).
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
> in one dashboard backed by one SQL query language. Built on Coral,
> with Llama 3.3 70B served by Groq doing the analysis."

## [0:20 – 0:45] The Coral foundation

*Switch to the terminal window. The query should already be in your
history — press Up arrow to recall it.*

```powershell
coral sql "SELECT schema_name AS source, COUNT(*) AS tables FROM coral.tables WHERE schema_name != 'coral' GROUP BY schema_name ORDER BY schema_name"
```

Expected output (one frame, no scrolling — perfect for the camera):

```
+----------------+--------+
| source         | tables |
+----------------+--------+
| devto          | 2      |
| github         | 362    |
| linear         | 8      |
| sentry         | 12     |
| slack          | 2      |
| slack_messages | 1      |
+----------------+--------+
```

> "Coral turns four developer APIs into SQL tables — GitHub, Linear,
> Sentry, Slack — that's 384 tables total. Plus my custom
> `slack_messages` source for queryable channel history, and the
> `devto` bounty source I submitted to Coral itself. ShipMind queries
> all of them at once."

*Pause for ~3 s on this output before switching back to the browser.
The `362` for GitHub is the visual hook — point at it if you like.*

## [0:45 – 1:10] The dashboard, already warm

*Switch to the browser. Scroll to the top.*

> "Here's the dashboard. The score is **20 — Hold**.
> Llama 3.3 70B generated this by looking at the results of all 5
> release checks at once."

*Point at the "Groq · Llama 3.3 70B" pill in the top right.*

> "That pill in the header shows the active LLM. I picked Groq for
> the demo because it's fast and free — Llama 3.3 70B comes back in
> about a second. The same architecture works on Anthropic if you'd
> rather use Claude."

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
titles next to real error titles, then the analysis from Llama.*

> "These are real merged PRs from the Coral repo cross-referenced with
> real errors. The analysis underneath is Llama reading the table and
> telling me what to actually do. The 'LLM analysis · Groq · Llama
> 3.3 70B' label tells you exactly which model produced it."

## [1:45 – 2:15] Team signals from Slack

*Click the **Team Signals** card.*

> "ShipMind also pulls what the team is saying about the release in
> Slack — release, deploy, ship, blocker keywords. Here are the
> messages from `#releases`."

*Scroll the table briefly so the audience sees real messages including
"blocker: JWT auth PR is still in review" and "deploy checklist for
v1.0".*

> "And here, Llama reads those messages and notes the JWT auth
> blocker explicitly — calls it out as the thing to fix before
> shipping."

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
> and one cross-source query. Built on Coral and Llama in four days."

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
- **LLM pill shows "no LLM (stub mode)"** → your `GROQ_API_KEY` env
  var isn't loaded. Check `.env` is at the project root and restart
  Flask.
