"""Run with: python -m streamlit run app.py"""

import logging
import sqlite3

import pandas as pd
import streamlit as st

from verity.database import initialize_database, read_records, vendor_payment_history
from verity.policies import POLICIES
from verity.requests import MAX_REQUEST_LENGTH, SAMPLES, validate_request

st.set_page_config(page_title="Verity | Payment assurance", page_icon="◈", layout="wide")
st.title("◈ Verity")
st.caption("An AI agent that verifies the real human behind every payment request.")
st.info("PHASE 1 · Foundation only · Fictional Northwind Corporation · No live AI or identity verification")

try:
    initialize_database()
    employees = read_records("employees")
    vendors = read_records("vendors")
    transactions = read_records("transactions")
except (sqlite3.Error, OSError, ValueError):
    logging.exception("Unable to load the fictional database")
    st.error("The demo database could not be loaded. Check the terminal for details and follow the README troubleshooting steps.")
    st.stop()

with st.sidebar:
    st.header("VERITY / NORTHWIND")
    page = st.radio("Workspace", ["Payment request", "Company records", "Transaction history", "Policies & roadmap", "Audit log"])
    st.divider()
    st.caption("MIST 5400 · University of Georgia")
    st.caption("Local classroom prototype. Use fictional information only. No payment can be executed.")


def display_records(records: list[dict]) -> None:
    frame = pd.DataFrame(records)
    for column in list(frame.columns):
        if column.endswith("_cents"):
            frame[column.removesuffix("_cents") + " (USD)"] = frame.pop(column).map(lambda amount: f"${amount / 100:,.2f}")
    frame.columns = [name.replace("_", " ").title() for name in frame.columns]
    st.dataframe(frame, hide_index=True, width="stretch")


def load_sample(name: str) -> None:
    st.session_state["request_text"] = SAMPLES[name]
    st.session_state.pop("request_preview", None)


if page == "Payment request":
    st.subheader("Review starts with a request")
    st.write("Explore the fictional company records, then prepare a sample payment request for the next phase.")
    columns = st.columns(3)
    for column, label, count in zip(columns, ["Employees", "Vendors", "Historical payments"], [len(employees), len(vendors), len(transactions)]):
        column.metric(label, count)
    st.markdown("#### Load a fictional example")
    for column, name in zip(st.columns(3), SAMPLES):
        column.button(name, on_click=load_sample, args=(name,), width="stretch")
    with st.form("payment_request"):
        text = st.text_area("Payment request", key="request_text", height=220,
                            max_chars=MAX_REQUEST_LENGTH,
                            placeholder="Paste a fictional request, including the sender, vendor and amount…")
        submitted = st.form_submit_button("Preview request", type="primary")
    if submitted:
        st.session_state.pop("request_preview", None)
        try:
            st.session_state["request_preview"] = validate_request(text)
        except ValueError as error:
            st.error(str(error))
    if "request_preview" in st.session_state:
        st.markdown("#### Submitted preview")
        st.code(st.session_state["request_preview"], language=None)
        st.warning("Preview only. This text has not been investigated or saved to the audit log. No risk score or payment recommendation has been generated.")
    st.caption("Request text stays in this browser session's server memory. Phase 2 will add Claude and clearly labeled offline rules.")

elif page == "Company records":
    st.subheader("Trusted company records")
    st.caption("Synthetic fixture data, frozen for a repeatable November 2026 demonstration. Account IDs are nonfunctional placeholders.")
    directory, suppliers = st.tabs(["Employee directory", "Vendor records"])
    with directory:
        department = st.selectbox("Department", ["All"] + sorted({row["department"] for row in employees}))
        display_records([row for row in employees if department == "All" or row["department"] == department])
    with suppliers:
        display_records(vendors)
        vendor = st.selectbox("Previous vendor payments", vendors, format_func=lambda row: row["company_name"])
        st.caption("Derived from transaction history. Cancelled payments are shown explicitly and are not completed payments.")
        display_records(vendor_payment_history(vendor["vendor_id"]))

elif page == "Transaction history":
    st.subheader("Historical payments")
    st.caption("100 fictional historical transactions; these are seed records, not payments processed by Verity.")
    status = st.selectbox("Payment status", ["All", "Paid", "Cancelled"])
    display_records([row for row in transactions if status == "All" or row["status"] == status])

elif page == "Policies & roadmap":
    st.subheader("Northwind payment policies")
    st.warning("Policy reference only in Phase 1. Automated policy enforcement is not implemented yet.")
    for policy_id, description in POLICIES:
        st.write(f"**{policy_id}** · {description}")
    st.divider()
    st.subheader("Implementation roadmap")
    st.write("**1 · Foundation:** SQLite, fictional records, request preview, and this dashboard.")
    st.write("**2 · AI investigation:** Claude integration, validated extraction, and investigation tools.")
    st.write("**3 · Verification and decisions:** simulated trusted-contact challenge, Python policy rules, risk scoring, human review, and audit persistence.")
    st.write("**4 · Evaluation:** 40 scenarios, separate live-AI and offline metrics, and measured results.")
    st.write("**5 · Demo preparation:** business case, final write-up, and presentation polish.")

elif page == "Audit log":
    st.subheader("Investigation audit log")
    st.info("No investigation audit records yet. Persistent investigation logging will be implemented in Phase 3. Request previews are not investigations.")

st.divider()
st.caption("FICTIONAL DATA · CLASSROOM PROTOTYPE · HUMAN REVIEW REQUIRED · NO REAL PAYMENTS")
