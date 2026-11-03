"""Application service: validated extraction -> read tools -> deterministic findings."""

import re
from dataclasses import asdict
from datetime import date
from pathlib import Path
from time import perf_counter

from verity.database import DEFAULT_DB, read_records, vendor_payment_history
from verity.extraction import offline_extract, validate_extraction
from verity.models import EvidenceSelection, Extraction, Investigation, InvestigationError, NoArguments
from verity.providers import ToolAgent
from verity.requests import validate_request
from verity.tools import check_policy, check_vendor_history, lookup_directory


def investigate(text: str, *, path: Path = DEFAULT_DB, agent: ToolAgent | None = None, as_of: date | None = None) -> Investigation:
    started = perf_counter()
    text = validate_request(text)
    as_of = as_of or date.today()
    employees = read_records("employees", path)
    vendors = read_records("vendors", path)
    trace = []

    def record(name: str, result: dict) -> None:
        trace.append({"tool": name, "status": "completed", "result": result})
        if agent:
            agent.record_result(result)

    def require_call(name: str, description: str) -> None:
        if agent:
            agent.call_tool(name, description, NoArguments)

    if agent:
        extracted = agent.call_tool("parse_request", "Extract verbatim payment-request details. Use null for missing/ambiguous fields.", Extraction)
    else:
        extracted = offline_extract(text, [e["full_name"] for e in employees], [v["company_name"] for v in vendors])
    parsed = validate_extraction(extracted, text)
    record("parse_request", {"extraction": parsed.extraction.model_dump(), "amount_cents": parsed.amount_cents, "warnings": parsed.warnings})

    require_call("lookup_directory", "Compare the validated sender against the local fictional directory.")
    employee, findings = lookup_directory(parsed, employees)
    record("lookup_directory", {"employee": employee, "findings": [asdict(f) for f in findings], "identity_verified": False})

    require_call("check_vendor_history", "Check the validated vendor, authorized account, and completed payment history.")
    matched = next((v for v in vendors if v["company_name"].casefold() == (parsed.extraction.vendor or "").casefold()), None)
    history = vendor_payment_history(matched["vendor_id"], path) if matched else []
    vendor, vendor_findings = check_vendor_history(parsed, vendors, history, as_of=as_of)
    findings.extend(vendor_findings)
    record("check_vendor_history", {"vendor": vendor, "as_of": as_of.isoformat(), "findings": [asdict(f) for f in vendor_findings]})

    require_call("check_policy", "Apply fixed Python policy checks. These cannot be waived by the model.")
    account_change = bool(re.search(r"(?:new|chang\w*|updat\w*|different).{0,40}(?:bank|account|payment details)|(?:bank|account|payment details).{0,40}(?:new|chang\w*|updat\w*|different)", text, re.I))
    policy_findings = check_policy(parsed, employee, account_change_mentioned=account_change)
    findings.extend(policy_findings)
    record("check_policy", {"findings": [asdict(f) for f in policy_findings], "decision": "not_implemented"})

    highlights = [f.code for f in findings if f.severity != "info"]
    if agent:
        selection = agent.call_tool("summarize_evidence", "Select existing evidence IDs to highlight. Every finding remains visible regardless of selection.", EvidenceSelection)
        if not set(selection.evidence_ids).issubset({f.code for f in findings}):
            raise InvestigationError("The AI referenced evidence that does not exist. No result was accepted.")
        highlights = list(dict.fromkeys(selection.evidence_ids))
        record("summarize_evidence", {"evidence_ids": highlights})

    return Investigation(text, "Live AI · OpenAI" if agent else "Offline demo · deterministic rules, not AI",
                         agent.model if agent else None, parsed, findings, trace,
                         employee, vendor, highlights, round(perf_counter() - started, 3))
