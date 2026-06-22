"""Prompt history management with SQLite.

Auto-creates lineart_history.db on first use.
Each prompt output is stored as a separate record.
"""

import csv
import json
import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "lineart_history.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS prompts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT    NOT NULL,
    mode        TEXT    NOT NULL,
    character   TEXT    NOT NULL DEFAULT '',
    char_label  TEXT    NOT NULL DEFAULT '',
    gender      TEXT    NOT NULL DEFAULT '',
    model       TEXT    NOT NULL DEFAULT '',
    lang        TEXT    NOT NULL DEFAULT '',
    ar          TEXT    NOT NULL DEFAULT '',
    output_type TEXT    NOT NULL DEFAULT '',
    prompt      TEXT    NOT NULL DEFAULT ''
);
"""

_conn: sqlite3.Connection | None = None


def _get_connection() -> sqlite3.Connection:
    """Get or create the database connection (lazy init)."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH))
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.executescript(SCHEMA_SQL)
        logger.info("History database initialized: %s", DB_PATH)
    return _conn


def close() -> None:
    """Close the database connection."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
        logger.info("History database closed.")


def save_prompt(
    mode: str,
    character: str,
    char_label: str,
    gender: str,
    model: str,
    lang: str,
    ar: str,
    output_type: str,
    prompt: str,
) -> int:
    """Save a generated prompt record. Returns the new record ID."""
    conn = _get_connection()
    cursor = conn.execute(
        """INSERT INTO prompts (created_at, mode, character, char_label, gender,
                                model, lang, ar, output_type, prompt)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            time.strftime("%Y-%m-%dT%H:%M:%S"),
            mode,
            character or "",
            char_label or "",
            gender or "",
            model or "",
            lang or "",
            ar or "",
            output_type or "",
            prompt or "",
        ),
    )
    conn.commit()
    rid = cursor.lastrowid
    assert rid is not None
    return rid


def get_history(
    page: int = 1,
    per_page: int = 20,
    model: str | None = None,
    output_type: str | None = None,
) -> dict:
    """Get paginated history records.

    Returns:
        dict with keys: items, total, page, pages, per_page
    """
    conn = _get_connection()
    conditions: list[str] = []
    params: list[str] = []

    if model:
        conditions.append("model = ?")
        params.append(model)
    if output_type:
        conditions.append("output_type = ?")
        params.append(output_type)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    # Total count
    total = conn.execute(f"SELECT COUNT(*) FROM prompts{where}", params).fetchone()[0]

    pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    rows = conn.execute(
        f"SELECT * FROM prompts{where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    items = [dict(r) for r in rows]
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
    }


def get_prompt(prompt_id: int) -> dict | None:
    """Get a single prompt record by ID."""
    conn = _get_connection()
    row = conn.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
    return dict(row) if row else None


def delete_prompt(prompt_id: int) -> bool:
    """Delete a prompt record. Returns True if deleted."""
    conn = _get_connection()
    cursor = conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    conn.commit()
    return cursor.rowcount > 0


def clear_history() -> int:
    """Delete all prompt records. Returns number of deleted records."""
    conn = _get_connection()
    count = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    conn.execute("DELETE FROM prompts")
    conn.commit()
    return count


def export_history(format: str = "json", filepath: str | None = None) -> str:
    """Export all history records.

    Args:
        format: 'json' or 'csv'
        filepath: Optional output file path. If None, returns string.

    Returns:
        Exported content as string.
    """
    conn = _get_connection()
    rows = conn.execute("SELECT * FROM prompts ORDER BY id DESC").fetchall()
    data = [dict(r) for r in rows]

    if format == "csv":
        return _export_csv(data, filepath)
    else:
        return _export_json(data, filepath)


def _export_json(data: list[dict], filepath: str | None = None) -> str:
    """Export as JSON."""
    content = json.dumps(data, ensure_ascii=False, indent=2)
    if filepath:
        Path(filepath).write_text(content, encoding="utf-8")
    return content


def _export_csv(data: list[dict], filepath: str | None = None) -> str:
    """Export as CSV."""
    if not data:
        return ""

    fieldnames = [
        "id", "created_at", "mode", "character", "char_label",
        "gender", "model", "lang", "ar", "output_type", "prompt",
    ]
    output = Path(filepath) if filepath else None

    import io

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    content = buf.getvalue()

    if output:
        output.write_text(content, encoding="utf-8-sig")
    return content
