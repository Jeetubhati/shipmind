import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GITHUB_ORG       = os.getenv("GITHUB_ORG", "")
GITHUB_REPO      = os.getenv("GITHUB_REPO", "")
LINEAR_ORG_SLUG  = os.getenv("LINEAR_ORG_SLUG", "")
SENTRY_ORG_SLUG  = os.getenv("SENTRY_ORG_SLUG", "") or os.getenv("SENTRY_ORG", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")
LINEAR_TEAM_KEY  = os.getenv("LINEAR_TEAM_KEY", "SHI")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

CORAL_CONTEXT = f"""
You query data using Coral SQL. Available sources and key tables:

GITHUB (owner filter required = '{GITHUB_ORG}'):
  github.user_repos — name, description, language, pushed_at, open_issues_count, stargazers_count
  github.pulls      — number, title, state, merged_at, created_at, user_login, label_names
                      REQUIRED FILTERS: owner, repo
  github.commits    — sha, message, author_name, author_date, additions, deletions
                      REQUIRED FILTERS: owner, repo
  github.issues     — number, title, state, body, created_at, closed_at, label_names
                      REQUIRED FILTERS: owner, repo
  github.repo_branches — name, commit_sha, commit_committed_date
                      REQUIRED FILTERS: owner, repo

SENTRY (org configured via env, not a WHERE filter):
  sentry.issues     — id, title, level, status, first_seen, last_seen, count,
                      culprit, project_slug
  sentry.projects   — id, name, slug, platform, date_created

LINEAR (note: state_name uses SINGLE underscore):
  linear.issues     — identifier, title, state_name, priority, assignee_name,
                      cycle_name, project_name, created_at, updated_at,
                      completed_at, team_key
  linear.projects   — name, state, description, target_date, lead_name
  linear.cycles     — number, name, starts_at, ends_at

SLACK (custom source with WHERE-friendly filter):
  slack_messages.messages — channel, ts, user, text, subtype, thread_ts, reply_count
                      REQUIRED FILTER: channel = '{SLACK_CHANNEL_ID}'
  slack.channels    — id, name, topic, purpose, num_members

RULES:
1. Always use LIMIT (default 25)
2. For date math: current_timestamp - INTERVAL '7 days'
3. Linear nested fields use single underscore: state_name, assignee_name
4. For JOINs across sources use LIKE with lower():
   lower(pr.title) LIKE '%' || lower(issue.identifier) || '%'
5. Return ONLY valid SQL. No markdown. No explanation.
"""
