"""SQLite adapter. The UI never constructs SQL or owns connections."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from verity.seed import employees, transactions, vendors

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "verity.sqlite3"
SCHEMA_VERSION = 1


@contextmanager
def connect(path: Path = DEFAULT_DB):
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(path: Path = DEFAULT_DB) -> None:
    """Create and seed once, atomically; later app reruns preserve local records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == SCHEMA_VERSION:
            return
        if version != 0:
            raise ValueError("Unsupported database version; use a compatible application version.")
        db.execute("""CREATE TABLE employees (
            employee_id TEXT PRIMARY KEY, full_name TEXT NOT NULL,
            job_title TEXT NOT NULL, department TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE, trusted_phone TEXT NOT NULL,
            approval_limit_cents INTEGER NOT NULL CHECK(approval_limit_cents >= 0))""")
        db.execute("""CREATE TABLE vendors (
            vendor_id TEXT PRIMARY KEY, company_name TEXT NOT NULL UNIQUE,
            payment_account TEXT NOT NULL, payment_frequency TEXT NOT NULL,
            last_bank_change TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Active', 'Suspended')))""")
        db.execute("""CREATE TABLE transactions (
            payment_id TEXT PRIMARY KEY,
            requester_id TEXT NOT NULL REFERENCES employees(employee_id),
            vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            payment_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Paid', 'Cancelled')))""")
        db.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees())
        db.executemany("INSERT INTO vendors VALUES (?, ?, ?, ?, ?, ?)", vendors())
        db.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)", transactions())
        db.execute("PRAGMA user_version = 1")


QUERIES = {
    "employees": "SELECT * FROM employees ORDER BY employee_id",
    "vendors": "SELECT * FROM vendors ORDER BY vendor_id",
    "transactions": """SELECT t.payment_id, e.full_name AS requester,
        v.company_name AS vendor, t.amount_cents, t.payment_date, t.status
        FROM transactions t JOIN employees e ON t.requester_id = e.employee_id
        JOIN vendors v ON t.vendor_id = v.vendor_id ORDER BY t.payment_date DESC""",
}


def read_records(collection: str, path: Path = DEFAULT_DB) -> list[dict]:
    if collection not in QUERIES:
        raise ValueError("Unknown record collection.")
    with connect(path) as db:
        return [dict(row) for row in db.execute(QUERIES[collection]).fetchall()]


def vendor_payment_history(vendor_id: str, path: Path = DEFAULT_DB) -> list[dict]:
    with connect(path) as db:
        return [dict(row) for row in db.execute(
            "SELECT payment_date, amount_cents, status FROM transactions "
            "WHERE vendor_id = ? ORDER BY payment_date DESC", (vendor_id,)
        ).fetchall()]


if __name__ == "__main__":
    initialize_database()
    print("Fictional database ready: 20 employees, 15 vendors, 100 transactions.")
