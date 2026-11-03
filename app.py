"""Run with: python -m streamlit run app.py"""

import logging
import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from verity.database import initialize_database, read_records, vendor_payment_history
from verity.investigation import investigate
from verity.models import InvestigationError
from verity.policies import POLICIES
from verity.providers import DEFAULT_MODEL, OpenAIToolAgent
from verity.requests import MAX_REQUEST_LENGTH, SAMPLES, validate_request
from verity.ui_investigation import render_investigation

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

st.set_page_config(page_title="Verity | Payment assurance", page_icon="◈", layout="wide")
st.title("◈ Verity")
st.caption("An AI agent that verifies the real human behind every payment request.")
st.info("PHASE 2 · Request investigation · Fictional Northwind Corporation · No real identity verification or payments")

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
    page = st.radio("Workspace", ["Payment request", "Investigation results", "Company records", "Transaction history", "Policies & roadmap", "Audit log"])
    mode = st.selectbox("Investigation mode", ["Offline demo (no AI)", "Live AI (OpenAI)"])
    live = mode == "Live AI (OpenAI)"
    if live:
        st.caption("Sends the request and matched fictional records to OpenAI. API usage may incur charges.")
    else:
        st.caption("Deterministic rules only. No API key, network call, or AI model is used.")
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
    st.session_state.pop("investigation", None)


if page == "Payment request":
    st.subheader("Review starts with a request")
    st.write("Submit a fictional payment request to check its sender, vendor history, and company policy requirements.")
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
        consent = st.checkbox("I agree to send this fictional request and matched records to OpenAI.") if live else False
        preview = st.form_submit_button("Preview request")
        submitted = st.form_submit_button("Investigate request", type="primary")
    if preview:
        st.session_state.pop("request_preview", None)
        st.session_state.pop("investigation", None)
        try:
            st.session_state["request_preview"] = validate_request(text)
        except ValueError as error:
            st.error(str(error))
    if submitted:
        st.session_state.pop("request_preview", None)
        st.session_state.pop("investigation", None)
        agent = None
        try:
            clean_text = validate_request(text)
            if live:
                if not consent:
                    raise InvestigationError("Please confirm sending fictional data before using live AI.")
                agent = OpenAIToolAgent(api_key=os.getenv("OPENAI_API_KEY", ""),
                                        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), request_text=clean_text)
            with st.spinner("Checking the request against fictional company records…"):
                st.session_state["investigation"] = investigate(clean_text, agent=agent)
        except (InvestigationError, ValueError) as error:
            st.error(str(error))
        except (sqlite3.Error, OSError):
            logging.exception("Investigation database access failed")
            st.error("Company records could not be read. No investigation was completed; check the local database.")
        finally:
            if agent:
                agent.close()
    if "request_preview" in st.session_state:
        st.markdown("#### Submitted preview")
        st.code(st.session_state["request_preview"], language=None)
        st.warning("Preview only. This text has not been investigated or saved to the audit log.")
    if "investigation" in st.session_state:
        render_investigation(st.session_state["investigation"])
    st.caption("Results refer to the submitted request shown in the result panel; edits require a new investigation.")

elif page == "Investigation results":
    if "investigation" in st.session_state:
        render_investigation(st.session_state["investigation"])
    else:
        st.info("No investigation in this session yet. Load a sample on Payment request and click Investigate request.")

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
    st.info("Python checks identify approval requirements and policy concerns. Approval collection and final decisions are not implemented yet.")
    for policy_id, description in POLICIES:
        st.write(f"**{policy_id}** · {description}")
    st.divider()
    st.subheader("Implementation roadmap")
    st.write("**1 · Foundation:** SQLite, fictional records, request preview, and this dashboard.")
    st.write("**2 · Investigation:** working offline rules and optional OpenAI tool calling, validated extraction, directory/vendor checks, and policy findings.")
    st.write("**3 · Verification and decisions:** simulated trusted-contact challenge, Python policy rules, risk scoring, human review, and audit persistence.")
    st.write("**4 · Evaluation:** 40 scenarios, separate live-AI and offline metrics, and measured results.")
    st.write("**5 · Demo preparation:** business case, final write-up, and presentation polish.")

elif page == "Audit log":
    st.subheader("Investigation audit log")
    st.info("Persistent investigation logging will be implemented in Phase 3. Current investigation results exist only in this session.")

st.divider()
st.caption("FICTIONAL DATA · CLASSROOM PROTOTYPE · HUMAN REVIEW REQUIRED · NO REAL PAYMENTS")
