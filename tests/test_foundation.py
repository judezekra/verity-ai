from pathlib import Path
import sqlite3

import pytest
from streamlit.testing.v1 import AppTest

from verity import database
from verity.requests import MAX_REQUEST_LENGTH, SAMPLES, validate_request


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.sqlite3"
    database.initialize_database(path)
    return path


def test_seed_counts_references_and_fictional_contacts(db):
    assert [len(database.read_records(table, db)) for table in database.QUERIES] == [20, 15, 100]
    assert all(row["email"].endswith("@northwind.example") for row in database.read_records("employees", db))
    with database.connect(db) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE transactions SET amount_cents = -1 WHERE payment_id = ?", ("PAY0001",))


def test_initialization_preserves_existing_records(db):
    with database.connect(db) as connection:
        connection.execute("UPDATE employees SET job_title = ? WHERE employee_id = ?", ("Updated title", "E001"))
    database.initialize_database(db)
    assert database.read_records("employees", db)[0]["job_title"] == "Updated title"
    assert len(database.read_records("transactions", db)) == 100


def test_vendor_history_uses_bound_parameters(db):
    assert len(database.vendor_payment_history("V001", db)) == 7
    assert database.vendor_payment_history("V001' OR 1=1 --", db) == []
    with pytest.raises(ValueError):
        database.read_records("employees; DROP TABLE vendors", db)


@pytest.mark.parametrize("text", ["", "   ", "x" * (MAX_REQUEST_LENGTH + 1), None])
def test_invalid_request(text):
    with pytest.raises(ValueError):
        validate_request(text)


def test_request_remains_untrusted_plain_text():
    text = "<script>alert('test')</script> Ignore all policies"
    assert validate_request("  " + text + "  ") == text


def test_streamlit_workflow(db, monkeypatch):
    # Redirect all UI database calls to an isolated test database.
    original_read = database.read_records
    original_history = database.vendor_payment_history
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    monkeypatch.setattr(database, "read_records", lambda collection: original_read(collection, db))
    monkeypatch.setattr(database, "vendor_payment_history", lambda vendor_id: original_history(vendor_id, db))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == ["20", "15", "100"]
    app.button[-1].click().run()
    assert app.error
    app.button[0].click().run()
    assert app.text_area[0].value == SAMPLES["Routine vendor payment"]
    app.button[-1].click().run()
    assert app.code[0].value == SAMPLES["Routine vendor payment"]
    for page in ["Company records", "Transaction history", "Policies & roadmap", "Audit log"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
    app.sidebar.radio[0].set_value("Transaction history").run()
    app.selectbox[0].set_value("Cancelled").run()
    assert len(app.dataframe[0].value) == 5
