import subprocess
import csv
import io
import time
import json


def _parse_table(raw: str) -> tuple[list[str], list[dict]]:
    """
    Parse coral sql's default ASCII-table output:

        +-----+-----+
        | col | col |
        +-----+-----+
        | val | val |
        +-----+-----+

    Returns (columns, rows). Falls back to (["output"], [{"output": line}, ...])
    when the shape doesn't match.
    """
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    border_lines = [i for i, ln in enumerate(lines) if ln.startswith("+") and set(ln) <= set("+-")]
    if len(border_lines) < 2:
        return ["output"], [{"output": ln} for ln in lines]

    if border_lines[0] + 1 == border_lines[1]:
        return [], []

    header_idx = border_lines[0] + 1
    header_line = lines[header_idx]
    columns = [c.strip() for c in header_line.strip("|").split("|")]

    rows: list[dict] = []
    for i, ln in enumerate(lines):
        if i <= border_lines[1] or ln.startswith("+"):
            continue
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) != len(columns):
            continue
        rows.append(dict(zip(columns, cells)))
    return columns, rows


def run_query(sql: str, timeout: int = 180) -> dict:
    """
    Execute a Coral SQL query.
    Returns: {
        "rows": list[dict],
        "raw": str,
        "columns": list[str],
        "row_count": int,
        "duration_ms": int,
        "error": str | None
    }
    """
    start = time.time()
    sql_clean = " ".join(sql.split())

    try:
        result = subprocess.run(
            ["coral", "sql", sql_clean],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        duration_ms = int((time.time() - start) * 1000)

        if result.returncode != 0:
            return {
                "rows": [], "raw": "", "columns": [],
                "row_count": 0, "duration_ms": duration_ms,
                "error": result.stderr.strip() or "Query failed",
            }

        raw = result.stdout.strip()
        if not raw:
            return {
                "rows": [], "raw": "", "columns": [],
                "row_count": 0, "duration_ms": duration_ms,
                "error": None,
            }

        if raw.lstrip().startswith("["):
            try:
                rows = json.loads(raw)
                columns = list(rows[0].keys()) if rows else []
                return {
                    "rows": rows, "raw": raw, "columns": columns,
                    "row_count": len(rows), "duration_ms": duration_ms,
                    "error": None,
                }
            except json.JSONDecodeError:
                pass

        if "\t" in raw and "+--" not in raw:
            reader = csv.DictReader(io.StringIO(raw), delimiter="\t")
            columns = list(reader.fieldnames or [])
            rows = [dict(r) for r in reader]
            return {
                "rows": rows, "raw": raw, "columns": columns,
                "row_count": len(rows), "duration_ms": duration_ms,
                "error": None,
            }

        columns, rows = _parse_table(raw)
        return {
            "rows": rows, "raw": raw, "columns": columns,
            "row_count": len(rows), "duration_ms": duration_ms,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {
            "rows": [], "raw": "", "columns": [],
            "row_count": 0, "duration_ms": timeout * 1000,
            "error": f"Query timed out after {timeout}s",
        }
    except FileNotFoundError:
        return {
            "rows": [], "raw": "", "columns": [],
            "row_count": 0, "duration_ms": 0,
            "error": "coral CLI not found. Is it installed and on PATH?",
        }


def check_connection() -> dict:
    """Verify Coral is running and sources are connected."""
    result = run_query(
        "SELECT schema_name, table_name FROM coral.tables ORDER BY 1, 2"
    )
    if result["error"]:
        return {"connected": False, "error": result["error"], "sources": []}

    sources = sorted({
        r.get("schema_name") for r in result["rows"]
        if r.get("schema_name") and r.get("schema_name") != "coral"
    })
    return {
        "connected": True,
        "error": None,
        "sources": sources,
        "tables": result["rows"],
    }
