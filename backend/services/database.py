"""
SQLite-based persistent storage for AI Cyber Investigation System.
Uses Python's built-in sqlite3 — no additional pip install needed.
"""
import sqlite3
import json
import os
import threading
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cybercrime_cases.db")
_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    with _lock:
        conn = get_conn()
        c = conn.cursor()

        # Cases table — stores full case JSON
        c.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id     TEXT PRIMARY KEY,
                victim_name TEXT,
                amount_lost REAL DEFAULT 0,
                scam_type   TEXT DEFAULT 'unknown',
                status      TEXT DEFAULT 'investigating',
                alert_type  TEXT DEFAULT 'none',
                submitted_at TEXT,
                completed_at TEXT,
                data        TEXT NOT NULL
            )
        """)

        # Approvals table
        c.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                case_id     TEXT,
                action      TEXT,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT,
                decided_at  TEXT,
                data        TEXT NOT NULL
            )
        """)

        # Evidence files table
        c.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id     TEXT NOT NULL,
                file_name   TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                file_type   TEXT,
                file_size   INTEGER,
                sha256_hash TEXT,
                uploaded_by TEXT DEFAULT 'system',
                uploaded_at TEXT,
                notes       TEXT
            )
        """)

        # Chain of custody log
        c.execute("""
            CREATE TABLE IF NOT EXISTS custody_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id     TEXT NOT NULL,
                evidence_id INTEGER,
                action      TEXT NOT NULL,
                actor       TEXT DEFAULT 'AI_System',
                timestamp   TEXT NOT NULL,
                details     TEXT
            )
        """)

        # Suspect watchlist
        c.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator   TEXT NOT NULL,
                type        TEXT NOT NULL,
                case_ids    TEXT DEFAULT '[]',
                risk_level  TEXT DEFAULT 'medium',
                added_at    TEXT,
                notes       TEXT,
                UNIQUE(indicator, type)
            )
        """)

        # Audit log
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id   TEXT,
                action    TEXT NOT NULL,
                actor     TEXT DEFAULT 'system',
                timestamp TEXT NOT NULL,
                details   TEXT
            )
        """)

        conn.commit()
        conn.close()


# ─────────────────────────────────────────────────────────────────
# Case CRUD
# ─────────────────────────────────────────────────────────────────

def save_case(case_id: str, case_data: dict):
    with _lock:
        conn = get_conn()
        try:
            fraud_prob = (
                case_data.get("fraud_classification", {}).get("fraud_probability")
                or case_data.get("final_scores", {}).get("fraud_probability")
            )
            scam_type = case_data.get("complaint_analysis", {}).get("scam_type", "unknown")
            try:
                amount = float(case_data.get("amount_lost", 0))
            except (ValueError, TypeError):
                amount = 0.0

            conn.execute("""
                INSERT INTO cases (case_id, victim_name, amount_lost, scam_type, status,
                    alert_type, submitted_at, completed_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    victim_name  = excluded.victim_name,
                    amount_lost  = excluded.amount_lost,
                    scam_type    = excluded.scam_type,
                    status       = excluded.status,
                    alert_type   = excluded.alert_type,
                    completed_at = excluded.completed_at,
                    data         = excluded.data
            """, (
                case_id,
                case_data.get("victim_name", "Unknown"),
                amount,
                scam_type,
                case_data.get("status", "investigating"),
                case_data.get("alert_type", "none"),
                case_data.get("submitted_at"),
                case_data.get("completed_at"),
                json.dumps(case_data)
            ))
            conn.commit()
        finally:
            conn.close()


def load_case(case_id: str) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT data FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        return json.loads(row["data"]) if row else None
    finally:
        conn.close()


def load_all_cases() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT data FROM cases ORDER BY submitted_at DESC").fetchall()
        return [json.loads(r["data"]) for r in rows]
    finally:
        conn.close()


def load_case_stats() -> dict:
    conn = get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) as n FROM cases").fetchone()["n"]
        active = conn.execute("SELECT COUNT(*) as n FROM cases WHERE status='investigating'").fetchone()["n"]
        complete = conn.execute("SELECT COUNT(*) as n FROM cases WHERE status='investigation_complete'").fetchone()["n"]
        critical = conn.execute(
            "SELECT COUNT(*) as n FROM cases WHERE alert_type IN ('critical','scam_network_alert')"
        ).fetchone()["n"]
        total_loss = conn.execute("SELECT COALESCE(SUM(amount_lost),0) as s FROM cases").fetchone()["s"]

        # Aggregate recovered amount safely from case JSONs
        total_recovered = 0.0
        rows = conn.execute("SELECT data FROM cases").fetchall()
        for r in rows:
            try:
                c_data = json.loads(r["data"])
                total_recovered += float(c_data.get("recovered_amount", 0.0))
            except:
                pass

        # By scam type
        by_type = conn.execute(
            "SELECT scam_type, COUNT(*) as cnt FROM cases GROUP BY scam_type"
        ).fetchall()

        # Recent 7 days
        recent = conn.execute(
            "SELECT DATE(submitted_at) as day, COUNT(*) as cnt FROM cases "
            "WHERE submitted_at >= DATE('now','-7 days') GROUP BY day ORDER BY day"
        ).fetchall()

        return {
            "total": total,
            "active": active,
            "complete": complete,
            "critical": critical,
            "total_loss": total_loss,
            "total_recovered": total_recovered,
            "by_scam_type": [{"type": r["scam_type"], "count": r["cnt"]} for r in by_type],
            "daily_trend": [{"day": r["day"], "count": r["cnt"]} for r in recent],
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# Approvals CRUD
# ─────────────────────────────────────────────────────────────────

def save_approval(approval_id: str, approval_data: dict):
    with _lock:
        conn = get_conn()
        try:
            conn.execute("""
                INSERT INTO approvals (approval_id, case_id, action, status, created_at, decided_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(approval_id) DO UPDATE SET
                    status     = excluded.status,
                    decided_at = excluded.decided_at,
                    data       = excluded.data
            """, (
                approval_id,
                approval_data.get("case_id"),
                approval_data.get("action"),
                approval_data.get("status", "pending"),
                approval_data.get("created_at"),
                approval_data.get("decided_at"),
                json.dumps(approval_data)
            ))
            conn.commit()
        finally:
            conn.close()


def load_pending_approvals() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT data FROM approvals WHERE status='pending' ORDER BY created_at DESC"
        ).fetchall()
        return [json.loads(r["data"]) for r in rows]
    finally:
        conn.close()


def load_all_approvals() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT data FROM approvals ORDER BY created_at DESC").fetchall()
        return [json.loads(r["data"]) for r in rows]
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# Evidence & Chain of Custody
# ─────────────────────────────────────────────────────────────────

def add_evidence(case_id: str, file_name: str, file_path: str,
                 file_type: str = None, file_size: int = 0,
                 sha256_hash: str = None, uploaded_by: str = "officer",
                 notes: str = "") -> int:
    with _lock:
        conn = get_conn()
        try:
            ts = datetime.now().isoformat()
            cursor = conn.execute("""
                INSERT INTO evidence (case_id, file_name, file_path, file_type, file_size,
                    sha256_hash, uploaded_by, uploaded_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (case_id, file_name, file_path, file_type, file_size,
                  sha256_hash, uploaded_by, ts, notes))
            ev_id = cursor.lastrowid

            # Auto-log custody entry
            conn.execute("""
                INSERT INTO custody_log (case_id, evidence_id, action, actor, timestamp, details)
                VALUES (?, ?, 'RECEIVED', ?, ?, ?)
            """, (case_id, ev_id, uploaded_by, ts,
                  f"Evidence '{file_name}' received. SHA256: {sha256_hash or 'N/A'}"))

            conn.commit()
            return ev_id
        finally:
            conn.close()


def get_evidence_list(case_id: str) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE case_id = ? ORDER BY uploaded_at", (case_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_custody_log(case_id: str) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM custody_log WHERE case_id = ? ORDER BY timestamp", (case_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# Suspect Watchlist
# ─────────────────────────────────────────────────────────────────

def add_to_watchlist(indicator: str, ind_type: str, case_id: str, risk_level: str = "medium", notes: str = ""):
    with _lock:
        conn = get_conn()
        try:
            existing = conn.execute(
                "SELECT id, case_ids FROM watchlist WHERE indicator=? AND type=?",
                (indicator, ind_type)
            ).fetchone()

            ts = datetime.now().isoformat()
            if existing:
                case_ids = json.loads(existing["case_ids"])
                if case_id not in case_ids:
                    case_ids.append(case_id)
                conn.execute(
                    "UPDATE watchlist SET case_ids=?, risk_level=? WHERE id=?",
                    (json.dumps(case_ids), risk_level, existing["id"])
                )
            else:
                conn.execute("""
                    INSERT INTO watchlist (indicator, type, case_ids, risk_level, added_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (indicator, ind_type, json.dumps([case_id]), risk_level, ts, notes))

            conn.commit()
        finally:
            conn.close()


def check_watchlist(indicators: list[str]) -> list[dict]:
    if not indicators:
        return []
    conn = get_conn()
    try:
        placeholders = ",".join("?" for _ in indicators)
        rows = conn.execute(
            f"SELECT * FROM watchlist WHERE indicator IN ({placeholders})",
            indicators
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["case_ids"] = json.loads(d["case_ids"])
            results.append(d)
        return results
    finally:
        conn.close()


def get_watchlist_all() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM watchlist ORDER BY added_at DESC"
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["case_ids"] = json.loads(d["case_ids"])
            results.append(d)
        return results
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────────────────────────

def log_audit(case_id: str, action: str, actor: str = "system", details: str = ""):
    with _lock:
        conn = get_conn()
        try:
            conn.execute("""
                INSERT INTO audit_log (case_id, action, actor, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            """, (case_id, action, actor, datetime.now().isoformat(), details))
            conn.commit()
        finally:
            conn.close()
