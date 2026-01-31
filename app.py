from flask import Flask, render_template, request, jsonify, g
import json
import os
import sqlite3
import time

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "data.sqlite3")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS shared_checks (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            checked TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    conn.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


init_db()


@app.teardown_appcontext
def close_db(_exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/packing')
def packing():
    return render_template('packing.html')

@app.route('/reservations')
def reservations():
    return render_template('reservations.html')


@app.get('/api/packing')
def get_packing():
    db = get_db()
    row = db.execute(
        "SELECT checked FROM shared_checks WHERE id = 1"
    ).fetchone()
    checked = json.loads(row["checked"]) if row else []
    return jsonify({"checked": checked})


@app.post('/api/packing')
def set_packing():
    data = request.get_json(silent=True) or {}
    checked = data.get("checked", [])
    if not isinstance(checked, list):
        return jsonify({"error": "checked must be a list"}), 400

    sanitized = []
    for item in checked:
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            sanitized.append(int(item))
            continue
        if isinstance(item, str) and item.isdigit():
            sanitized.append(int(item))

    payload = json.dumps(sorted(set(sanitized)))
    now = int(time.time())
    db = get_db()
    db.execute(
        """
        INSERT INTO shared_checks (id, checked, updated_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            checked = excluded.checked,
            updated_at = excluded.updated_at
        """,
        (payload, now),
    )
    db.commit()
    return jsonify({"ok": True})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
