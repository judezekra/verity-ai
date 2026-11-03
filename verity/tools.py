"""Read-only investigation tools. No HTTP or UI; records arrive through the service."""

from datetime import date

from verity.models import Finding, ParsedRequest
from verity.policies import ADDITIONAL_APPROVAL_THRESHOLD_CENTS

RECENT_BANK_CHANGE_DAYS = 30
UNUSUAL_AMOUNT_MULTIPLIER = 3


def lookup_directory(request: ParsedRequest, employees: list[dict]) -> tuple[dict | None, list[Finding]]:
    info = request.extraction
    by_name = next((e for e in employees if e["full_name"].casefold() == (info.claimed_sender or "").casefold()), None)
    by_email = next((e for e in employees if e["email"].casefold() == (info.sender_email or "").casefold()), None)
    findings = []
    if by_email is None:
        findings.append(Finding("sender_unknown", "alert", "Employee directory", "The submitted sender email is not in the authorized directory."))
    if by_name and by_email and by_name["employee_id"] == by_email["employee_id"]:
        findings.append(Finding("sender_match", "info", "Employee directory", "Claimed name and email match one directory employee. This does not verify identity."))
        employee = by_name
    elif by_name:
        findings.append(Finding("sender_mismatch", "alert", "Employee directory", "The claimed employee's authorized email does not match the sender header."))
        employee = by_name
    elif by_email:
        findings.append(Finding("name_unconfirmed", "review", "Employee directory", "Sender email matches a record, but the claimed name is absent or different."))
        employee = by_email
    else:
        employee = None
    return employee, findings


def check_vendor_history(request: ParsedRequest, vendors: list[dict], history: list[dict], *, as_of: date) -> tuple[dict | None, list[Finding]]:
    vendor = next((v for v in vendors if v["company_name"].casefold() == (request.extraction.vendor or "").casefold()), None)
    if vendor is None:
        return None, [Finding("vendor_unknown", "review", "Vendor database", "No unique vendor match was established; confirm the vendor before proceeding.")]
    findings = [Finding("vendor_match", "info", "Vendor database", f"Matched {vendor['company_name']} ({vendor['vendor_id']}); usual frequency: {vendor['payment_frequency']}.")]
    if vendor["status"] != "Active":
        findings.append(Finding("vendor_suspended", "alert", "Vendor database", "This vendor is suspended."))
    days = (as_of - date.fromisoformat(vendor["last_bank_change"])).days
    if days < 0:
        findings.append(Finding("bank_date_future", "review", "Vendor database", "The recorded bank-change date is in the future; review data quality."))
    elif days <= RECENT_BANK_CHANGE_DAYS:
        findings.append(Finding("recent_bank_change", "review", "Vendor database", f"Vendor bank details changed {days} days before the investigation date; independent verification is required."))
    account = request.extraction.payment_account
    if account and account != vendor["payment_account"]:
        findings.append(Finding("account_mismatch", "alert", "Vendor database", "The requested payment account differs from the authorized account on file."))
    elif not account:
        findings.append(Finding("account_not_supplied", "info", "Vendor database", "No unique explicit account was extracted. Any later payment must use independently confirmed account details."))
    paid = [row["amount_cents"] for row in history if row["status"] == "Paid"]
    if paid:
        average = sum(paid) // len(paid)
        findings.append(Finding("vendor_history", "info", "Transaction history", f"{len(paid)} completed payments; average ${average / 100:,.2f}; range ${min(paid) / 100:,.2f}–${max(paid) / 100:,.2f}. Cancelled payments excluded."))
        if request.amount_cents is not None and request.amount_cents * len(paid) > sum(paid) * UNUSUAL_AMOUNT_MULTIPLIER:
            findings.append(Finding("unusual_amount", "review", "Transaction history", f"Requested amount exceeds {UNUSUAL_AMOUNT_MULTIPLIER} times the historical mean. This is a heuristic, not proof of fraud."))
    else:
        findings.append(Finding("no_paid_history", "review", "Transaction history", "No completed payment history exists for this vendor."))
    return vendor, findings


def check_policy(request: ParsedRequest, employee: dict | None, *, account_change_mentioned: bool) -> list[Finding]:
    findings = []
    amount = request.amount_cents
    if amount is not None and amount > ADDITIONAL_APPROVAL_THRESHOLD_CENTS:
        findings.append(Finding("additional_approval", "review", "Policy P01", f"Payment exceeds ${ADDITIONAL_APPROVAL_THRESHOLD_CENTS / 100:,.0f} and requires additional approval. This app has not collected that approval."))
    if amount is not None and employee and amount > employee["approval_limit_cents"]:
        findings.append(Finding("authority_exceeded", "alert", "Policy P05", f"Payment exceeds the claimed employee's ${employee['approval_limit_cents'] / 100:,.2f} approval authority."))
    if account_change_mentioned:
        findings.append(Finding("bank_change_request", "review", "Policy P02", "The message mentions changing payment details; independent verification is required."))
    if request.extraction.urgency_quotes or request.extraction.secrecy_quotes:
        findings.append(Finding("sensitive_language", "review", "Policy P04", "Urgency or secrecy language requires review. Legitimate requests can also contain this language."))
    for index, warning in enumerate(request.warnings):
        findings.append(Finding(f"input_{index}", "review", "Input validation", warning))
    findings.append(Finding("human_review", "review", "Policy P06", "Identity is unverified and human review is still required. Phase 2 produces findings, not a payment decision."))
    return findings
