import os
import sys

from flask import Flask, jsonify, render_template

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

from coral_runner import check_connection, run_query  # noqa: E402
from queries import RELEASE_QUERIES  # noqa: E402
from analyzer import analyze_results, get_llm_info, run_full_release_check  # noqa: E402

app = Flask(__name__)


@app.route("/")
def index():
    conn = check_connection()
    return render_template(
        "index.html",
        sources=conn.get("sources", []),
        connected=conn["connected"],
        queries=RELEASE_QUERIES,
        llm=get_llm_info(),
    )


@app.route("/api/status")
def status():
    payload = check_connection()
    payload["llm"] = get_llm_info()
    return jsonify(payload)


@app.route("/api/query/<query_name>")
def run_single_query(query_name):
    if query_name not in RELEASE_QUERIES:
        return jsonify({"error": f"Unknown query: {query_name}"}), 404

    q = RELEASE_QUERIES[query_name]
    result = run_query(q["sql"])
    analysis = (
        analyze_results(result, q["insight_prompt"])
        if not result.get("error")
        else None
    )

    return jsonify({
        "key": query_name,
        "title": q["title"],
        "description": q["description"],
        "sql": q["sql"].strip(),
        "data": result,
        "analysis": analysis,
    })


@app.route("/api/check", methods=["POST"])
def full_check():
    results = run_full_release_check(RELEASE_QUERIES)
    output = {"score": results["score"], "checks": {}}
    for key, check in results["checks"].items():
        output["checks"][key] = {
            "key": key,
            "title": check["title"],
            "description": check["description"],
            "sql": check["sql"].strip(),
            "row_count": check["data"]["row_count"],
            "duration_ms": check["data"]["duration_ms"],
            "columns": check["data"]["columns"],
            "rows": check["data"]["rows"][:20],
            "error": check["data"]["error"],
            "analysis": check["analysis"],
        }
    return jsonify(output)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
