-- THE MONEY QUERY: Release Readiness Check
-- Linear issues (what's planned) vs GitHub PRs (what's actually merged)
-- NOTE: Linear uses `state_name` (single underscore), not `state__name`.
-- NOTE: github.pulls filters are by `owner` + `repo` (string literals).
-- Day 2 will likely need a smarter join key — Linear identifiers rarely
-- appear verbatim in PR titles unless the team enforces a convention.
SELECT
  l.identifier  AS ticket_id,
  l.title       AS feature_name,
  l.state_name  AS linear_status,
  l.priority    AS priority,
  p.number      AS pr_number,
  p.state       AS pr_state,
  p.merged_at   AS merged_at,
  p.title       AS pr_title
FROM linear.issues l
LEFT JOIN github.pulls p
  ON p.owner = 'Jeetubhati'
  AND p.repo = 'coral'
  AND lower(p.title) LIKE '%' || lower(l.identifier) || '%'
WHERE l.team_key = 'SHI'
ORDER BY l.priority ASC, l.state_name
LIMIT 20;
