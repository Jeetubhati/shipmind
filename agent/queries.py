from config import GITHUB_ORG, GITHUB_REPO, SENTRY_ORG_SLUG, SLACK_CHANNEL_ID, LINEAR_TEAM_KEY

RELEASE_QUERIES = {

    "blockers": {
        "title": "Release Blockers",
        "description": "Open Sentry errors that could block this release",
        "sql": f"""
SELECT
  s.title              AS error_title,
  s.level              AS severity,
  s.count              AS occurrences,
  s.first_seen         AS first_seen,
  s.last_seen          AS last_seen,
  s.project            AS project
FROM sentry.issues s
WHERE s.status = 'unresolved'
  AND s.level IN ('fatal', 'error')
ORDER BY
  CASE s.level WHEN 'fatal' THEN 0 WHEN 'error' THEN 1 ELSE 2 END,
  s.count DESC
LIMIT 20
""",
        "insight_prompt": "What are the most critical release blockers? Which errors need immediate attention before shipping?",
    },

    "readiness": {
        "title": "Release Readiness",
        "description": "Linear issues vs GitHub PRs — what's done vs what's actually merged",
        "sql": f"""
SELECT
  l.identifier          AS ticket,
  l.title               AS feature,
  l.state_name          AS linear_state,
  l.priority            AS priority,
  p.number              AS pr_number,
  p.state               AS pr_state,
  p.merged_at           AS merged_at
FROM linear.issues l
LEFT JOIN github.pulls p
  ON p.owner = '{GITHUB_ORG}'
  AND p.repo = '{GITHUB_REPO}'
  AND lower(p.title) LIKE '%' || lower(l.identifier) || '%'
WHERE l.state_name IN ('In Progress', 'In Review', 'Done', 'Todo', 'Backlog')
ORDER BY l.priority ASC, l.state_name
LIMIT 25
""",
        "insight_prompt": "Is this release ready to ship? List features marked done in Linear but not merged in GitHub as risks.",
    },

    "risk": {
        "title": "Risk Assessment",
        "description": "Recent code changes with associated errors — what might break",
        "sql": f"""
SELECT
  p.title               AS pr_title,
  p.merged_at           AS merged,
  p.user__login         AS author,
  s.title               AS error_after_merge,
  s.level               AS error_level,
  s.count               AS occurrences,
  s.first_seen          AS error_first_seen
FROM github.pulls p
JOIN sentry.issues s
  ON CAST(s.first_seen AS TIMESTAMP) >= CAST(p.merged_at AS TIMESTAMP)
  AND CAST(s.first_seen AS TIMESTAMP) <= CAST(p.merged_at AS TIMESTAMP) + INTERVAL '7 days'
  AND s.level IN ('fatal', 'error')
WHERE p.owner = '{GITHUB_ORG}'
  AND p.repo = '{GITHUB_REPO}'
  AND p.state = 'closed'
  AND p.merged_at IS NOT NULL
  AND CAST(p.merged_at AS TIMESTAMP) >= current_timestamp - INTERVAL '30 days'
ORDER BY p.merged_at DESC, s.level
LIMIT 20
""",
        "insight_prompt": "Which recent PRs introduced errors after merging? What patterns in code changes correlate with production errors? What should we be careful about in this release?",
    },

    "signals": {
        "title": "Team Signals",
        "description": "Slack discussions about this release — what the team is saying",
        "sql": f"""
SELECT
  m.text            AS message,
  m.ts              AS timestamp,
  m.user            AS user
FROM slack_messages.messages m
WHERE m.channel = '{SLACK_CHANNEL_ID}'
  AND (
    lower(m.text) LIKE '%release%'
    OR lower(m.text) LIKE '%deploy%'
    OR lower(m.text) LIKE '%ship%'
    OR lower(m.text) LIKE '%broken%'
    OR lower(m.text) LIKE '%blocker%'
  )
ORDER BY m.ts DESC
LIMIT 25
""",
        "insight_prompt": "What is the team discussing about this release? Are there any concerns, blockers, or important context mentioned in Slack?",
    },

    "velocity": {
        "title": "Sprint Velocity",
        "description": "How fast is the team delivering — Linear issue state distribution",
        "sql": f"""
SELECT
  l.team_key              AS team,
  l.state_name            AS status,
  COUNT(*)                AS issue_count
FROM linear.issues l
WHERE l.team_key = '{LINEAR_TEAM_KEY}'
GROUP BY l.team_key, l.state_name
ORDER BY l.state_name
LIMIT 30
""",
        "insight_prompt": "What is the team's completion rate this sprint? Are they on track to finish planned work before the release date?",
    },
}
