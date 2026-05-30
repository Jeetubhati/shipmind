# ShipMind — submission checklist

Fill the blanks as you go. Anything `<…>` is a placeholder.

## Core (required)

- [ ] GitHub repo public: `https://github.com/Jeetubhati/shipmind`
- [ ] Repo README + screenshot in place
- [ ] Demo video uploaded (Loom or YouTube Unlisted): `<URL>`
- [ ] Registered on the WeMakeDevs hackathon page
- [ ] ⭐ Starred `withcoral/coral`
- [ ] Joined the Coral Discord (and introduced yourself in `#introductions`)

## Hackathon form (https://wemakedevs.org/hackathons/coral)

- **Track:** Track 1 — Enterprise Agent
- **Project name:** ShipMind
- **Tagline (≤140 chars):**
  > Know before you ship — joins GitHub, Linear, Sentry, Slack in one Coral SQL query, then asks Claude to score the release.
- **GitHub:** `https://github.com/Jeetubhati/shipmind`
- **Demo:** `<demo video URL>`
- **Description (≤280 chars):**
  > Release intelligence agent for engineering teams. Joins GitHub PRs, Linear issues, Sentry errors, and Slack signals in one Coral SQL query to answer: is this safe to ship? Includes 0–100 readiness score and Claude-powered analysis.

## Bounties

- [ ] **Custom source spec** — `dev.to (Forem)` PR opened to
      `withcoral/coral`:
      `https://github.com/withcoral/coral/compare/main...Jeetubhati:coral:feat/sources/community/devto?expand=1`
- [ ] **Blog post published** on dev.to: `<URL>`
- [ ] **Blog post shared** on LinkedIn, tagging `@Coral` and `@WeMakeDevs`: `<URL>`
- [ ] **Blog post shared** on X/Twitter, tagging `@withcoral`: `<URL>`
- [ ] **Discord `#how-i-coral` showcase post** (screenshots + the
      cross-source JOIN SQL): top 50 get a Claude Max 1-month voucher.

## Self-assessment vs judging criteria

- [x] **Potential Impact** — every engineering team ships code; the
      4-tab release ritual is universal.
- [x] **Creativity** — proactive release-gate, not a reactive incident
      tool.
- [x] **Technical** — 6 sources total (4 bundled + 2 custom-authored),
      real cross-source JOINs, working Flask web app, Claude analysis
      layer with no-key fallback.
- [x] **Best Use of Coral** — the GitHub ⋈ Sentry time-overlap JOIN
      and the Linear ⋈ GitHub identifier-LIKE JOIN are the unique value
      props; impossible without Coral.
- [x] **Aesthetics** — dark dashboard, animated score gauge,
      severity-coloured tables, no external dependencies.
- [x] **Learning** — first enterprise agent; the blog post walks
      through the schema-discovery journey honestly.

## Demo video must show

- [ ] `coral sql` listing the connected sources / tables
- [ ] At least one cross-source JOIN query visible (recommended: the
      risk-assessment query — GitHub ⋈ Sentry)
- [ ] The web dashboard with the score gauge populated
- [ ] At least 3 of the 5 cards showing real data
- [ ] Claude analysis text visible on at least one card
- [ ] The SQL `<details>` panel expanded on at least one card

## Things that are easy to forget

- Replace `docs/dashboard.png` with a real screenshot before pushing
  the repo (currently a placeholder reference in `README.md`).
- Make sure `.env` is **not** committed (`git status` should not list
  it; `.gitignore` does cover it).
- The PR commit message is fine but the GitHub PR description should
  also include a one-paragraph "why" — judges may read the PR rather
  than the README.
- Tell the Coral Discord that you opened a community source PR. They
  often surface those for visibility.
