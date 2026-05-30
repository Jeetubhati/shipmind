import json
import anthropic
from config import ANTHROPIC_API_KEY, CORAL_CONTEXT, CLAUDE_MODEL
from coral_runner import run_query

_PLACEHOLDER_KEYS = {"", "your_key_here", "your_key", "sk-ant-..."}
_has_real_key = ANTHROPIC_API_KEY and ANTHROPIC_API_KEY.strip() not in _PLACEHOLDER_KEYS
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if _has_real_key else None


def analyze_results(query_result: dict, prompt: str, context: str = "") -> str:
    """Use Claude to analyze Coral query results and produce insights."""
    if query_result.get("error"):
        return f"Query failed: {query_result['error']}"

    if query_result["row_count"] == 0:
        return "No data found for this query. The sources may have no matching records."

    if client is None:
        return _stub_analysis(query_result)

    data_summary = f"""
Query returned {query_result['row_count']} rows in {query_result['duration_ms']}ms.

Columns: {', '.join(query_result['columns'])}

Data (first 30 rows):
{json.dumps(query_result['rows'][:30], indent=2, default=str)}
"""

    messages = [{
        "role": "user",
        "content": f"""{prompt}

{context}

Here is the data from the Coral SQL query:
{data_summary}

Provide a concise, actionable analysis in 4-6 bullet points.
Focus on what the team needs to DECIDE or DO before shipping.
Use specific numbers and names from the data.
End with a one-line recommendation: SHIP / HOLD / SHIP WITH CAUTION.""",
    }]

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=messages,
        )
        return response.content[0].text.strip()
    except Exception as exc:
        return f"Claude analysis unavailable: {exc.__class__.__name__}: {exc}"


def _stub_analysis(query_result: dict) -> str:
    """Cheap deterministic summary when Claude is unavailable. Lets demo run offline."""
    rc = query_result["row_count"]
    cols = ", ".join(query_result["columns"][:5])
    return (
        "Claude API key not configured — showing raw query summary.\n\n"
        f"- {rc} rows returned in {query_result['duration_ms']}ms\n"
        f"- Columns: {cols}\n"
        "- Set ANTHROPIC_API_KEY in .env for full release analysis.\n"
        "Recommendation: SHIP WITH CAUTION"
    )


def generate_release_score(all_results: dict) -> dict:
    """Generate an overall release readiness score (0-100) from all query results."""
    summaries = {}
    for key, result in all_results.items():
        if not result.get("error") and result.get("row_count", 0) > 0:
            summaries[key] = {
                "rows": result["row_count"],
                "sample": result["rows"][:5],
            }

    if not summaries:
        return {"score": 50, "verdict": "UNKNOWN", "reasoning": "Insufficient data"}

    if client is None:
        total_rows = sum(s["rows"] for s in summaries.values())
        return {
            "score": 65,
            "verdict": "SHIP WITH CAUTION",
            "reasoning": (
                f"Stub score (Claude key not configured). "
                f"{len(summaries)}/5 checks returned data; {total_rows} rows total."
            ),
        }

    prompt = f"""
Based on this release intelligence data, give a release readiness score.

Data summary:
{json.dumps(summaries, indent=2, default=str)}

Respond with ONLY valid JSON in this exact format:
{{
  "score": <integer 0-100>,
  "verdict": "<SHIP | SHIP WITH CAUTION | HOLD>",
  "reasoning": "<one sentence explaining the score>"
}}
"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return {
            "score": 60,
            "verdict": "SHIP WITH CAUTION",
            "reasoning": "Could not parse release score — review data manually.",
        }
    except Exception as exc:
        return {
            "score": 60,
            "verdict": "SHIP WITH CAUTION",
            "reasoning": f"Score model error: {exc.__class__.__name__}",
        }


def run_full_release_check(queries: dict) -> dict:
    """Run all release queries and analyze each one."""
    results = {}

    for key, query_def in queries.items():
        print(f"  Running: {query_def['title']}...")
        query_result = run_query(query_def["sql"])
        analysis = analyze_results(query_result, query_def["insight_prompt"])
        results[key] = {
            "title": query_def["title"],
            "description": query_def["description"],
            "sql": query_def["sql"],
            "data": query_result,
            "analysis": analysis,
        }

    score = generate_release_score({k: v["data"] for k, v in results.items()})
    return {"checks": results, "score": score}
