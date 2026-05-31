"""Release-intelligence analyzer. Talks to Groq (preferred) or Anthropic.

Provider precedence:
  1. GROQ_API_KEY set      → use Groq via the OpenAI-compatible API (Llama 3.3 70B by default).
  2. ANTHROPIC_API_KEY set → use Anthropic (Claude Sonnet 4.6 by default).
  3. Neither set           → return a deterministic stub so the dashboard
                             still demos without any credit balance.
"""
import json

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    CORAL_CONTEXT,  # noqa: F401  — kept importable for callers that want it
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
)
from coral_runner import run_query

_PLACEHOLDERS = {
    "", "your_key_here", "your_key", "sk-ant-...", "sk-ant-your-key-here",
    "gsk_your_key_here",
}


def _is_real(key: str) -> bool:
    return bool(key and key.strip() not in _PLACEHOLDERS)


def _make_client():
    """Pick a provider. Returns (kind, client, model) or (None, None, None)."""
    if _is_real(GROQ_API_KEY):
        from openai import OpenAI
        return "groq", OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL), GROQ_MODEL
    if _is_real(ANTHROPIC_API_KEY):
        import anthropic
        return "anthropic", anthropic.Anthropic(api_key=ANTHROPIC_API_KEY), CLAUDE_MODEL
    return None, None, None


_PROVIDER, _CLIENT, _MODEL = _make_client()


def _chat(user_content: str, max_tokens: int = 600) -> str:
    """Call the active provider with a single user-content message. Returns text."""
    if _PROVIDER == "groq":
        resp = _CLIENT.chat.completions.create(
            model=_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user_content}],
        )
        return resp.choices[0].message.content.strip()
    if _PROVIDER == "anthropic":
        resp = _CLIENT.messages.create(
            model=_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user_content}],
        )
        return resp.content[0].text.strip()
    raise RuntimeError("no provider configured")


def analyze_results(query_result: dict, prompt: str, context: str = "") -> str:
    if query_result.get("error"):
        return f"Query failed: {query_result['error']}"

    if query_result["row_count"] == 0:
        return "No data found for this query. The sources may have no matching records."

    if _PROVIDER is None:
        return _stub_analysis(query_result)

    data_summary = (
        f"Query returned {query_result['row_count']} rows "
        f"in {query_result['duration_ms']}ms.\n\n"
        f"Columns: {', '.join(query_result['columns'])}\n\n"
        f"Data (first 30 rows):\n"
        f"{json.dumps(query_result['rows'][:30], indent=2, default=str)}"
    )

    user_content = (
        f"{prompt}\n\n{context}\n\n"
        f"Here is the data from the Coral SQL query:\n{data_summary}\n\n"
        "Provide a concise, actionable analysis in 4-6 bullet points.\n"
        "Focus on what the team needs to DECIDE or DO before shipping.\n"
        "Use specific numbers and names from the data.\n"
        "End with a one-line recommendation: SHIP / HOLD / SHIP WITH CAUTION."
    )

    try:
        return _chat(user_content, max_tokens=600)
    except Exception as exc:
        return f"Analysis unavailable ({_PROVIDER}): {exc.__class__.__name__}: {exc}"


def _stub_analysis(query_result: dict) -> str:
    """Cheap deterministic summary when no LLM key is configured."""
    rc = query_result["row_count"]
    cols = ", ".join(query_result["columns"][:5])
    return (
        "No LLM key configured — showing raw query summary.\n\n"
        f"- {rc} rows returned in {query_result['duration_ms']}ms\n"
        f"- Columns: {cols}\n"
        "- Set GROQ_API_KEY or ANTHROPIC_API_KEY in .env for full analysis.\n"
        "Recommendation: SHIP WITH CAUTION"
    )


def generate_release_score(all_results: dict) -> dict:
    summaries = {}
    for key, result in all_results.items():
        if not result.get("error") and result.get("row_count", 0) > 0:
            summaries[key] = {
                "rows": result["row_count"],
                "sample": result["rows"][:5],
            }

    if not summaries:
        return {"score": 50, "verdict": "UNKNOWN", "reasoning": "Insufficient data"}

    if _PROVIDER is None:
        total_rows = sum(s["rows"] for s in summaries.values())
        return {
            "score": 65,
            "verdict": "SHIP WITH CAUTION",
            "reasoning": (
                f"Stub score (no LLM key configured). "
                f"{len(summaries)}/5 checks returned data; {total_rows} rows total."
            ),
        }

    user_content = (
        "Based on this release intelligence data, give a release readiness score.\n\n"
        f"Data summary:\n{json.dumps(summaries, indent=2, default=str)}\n\n"
        "Respond with ONLY valid JSON in this exact format:\n"
        '{\n  "score": <integer 0-100>,\n'
        '  "verdict": "<SHIP | SHIP WITH CAUTION | HOLD>",\n'
        '  "reasoning": "<one sentence explaining the score>"\n}'
    )

    try:
        text = _chat(user_content, max_tokens=200)
        text = text.replace("```json", "").replace("```", "").strip()
        # Some models prepend a sentence before the JSON — find the first {.
        if not text.startswith("{"):
            i = text.find("{")
            if i >= 0:
                text = text[i:]
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
            "reasoning": f"Score model error ({_PROVIDER}): {exc.__class__.__name__}",
        }


def run_full_release_check(queries: dict) -> dict:
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
