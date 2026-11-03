"""Conservative offline parsing and common grounding checks for both modes."""

import re
from decimal import Decimal

from verity.models import Extraction, InvestigationError, ParsedRequest

EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
USD = re.compile(r"(?<![\w.-])(?:\$|USD\s+)(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?(?![\w,]|\.\d)", re.I)
URGENCY = re.compile(r"\b(?:urgent|immediately|today|emergency|right now|within an hour)\b", re.I)
SECRECY = re.compile(r"\b(?:confidential|secret|do not discuss|don't tell|email only|bypass approval)\b", re.I)
INJECTION = re.compile(r"ignore (?:all |previous |prior )?(?:instructions|policies|rules)|system prompt|developer message|mark (?:this )?(?:safe|approved)|override (?:the )?(?:policy|rules)", re.I)


def unique_match(values: list[str], text: str) -> str | None:
    matches = [match.group() for value in values
               if (match := re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text, re.I))]
    return matches[0] if len(matches) == 1 else None


def header_email(text: str) -> str | None:
    headers = re.findall(r"^From:\s*(.*)$", text, re.I | re.M)
    emails = EMAIL.findall(headers[0]) if len(headers) == 1 else []
    return emails[0] if len(emails) == 1 else None


def usd_amounts(text: str) -> list[str]:
    return list(dict.fromkeys(match.group() for match in USD.finditer(text)))


def offline_extract(text: str, employee_names: list[str], vendor_names: list[str]) -> Extraction:
    """Recognizes explicit USD amounts and exact fixture names; does not infer."""
    amounts = usd_amounts(text)
    accounts = list(dict.fromkeys(re.findall(r"\bDEMO-ACCOUNT-\d{4}\b", text)))
    actions = [line.strip() for line in text.splitlines()
               if re.search(r"\b(?:pay|payment|transfer|wire|schedule|arrange)\b", line, re.I)
               and not line.lower().startswith(("from:", "subject:"))]
    return Extraction(
        claimed_sender=unique_match(employee_names, text), sender_email=header_email(text),
        amount_text=amounts[0] if len(amounts) == 1 else None,
        vendor=unique_match(vendor_names, text),
        payment_account=accounts[0] if len(accounts) == 1 else None,
        urgency_quotes=[m.group() for m in URGENCY.finditer(text)][:8],
        secrecy_quotes=[m.group() for m in SECRECY.finditer(text)][:8],
        requested_actions=actions[:8],
    )


def validate_extraction(extracted: Extraction, text: str) -> ParsedRequest:
    """Ground model claims in input and independently check sender/amount ambiguity."""
    for value in extracted.model_dump().values():
        strings = value if isinstance(value, list) else [value]
        for item in strings:
            if item is not None and (not item.strip() or item not in text or len(item) > 1000):
                raise InvestigationError("Extraction could not be grounded in the request. No investigation was completed.")
    warnings = []
    header = header_email(text)
    if extracted.sender_email and header and extracted.sender_email.casefold() != header.casefold():
        raise InvestigationError("The AI sender conflicts with the From header. Review the request manually.")
    # The From header is the only supported sender source, not emails embedded in the body.
    extracted = extracted.model_copy(update={"sender_email": header})
    if header is None:
        warnings.append("A single unambiguous From email header is required.")
    amounts = usd_amounts(text)
    amount = None
    if len(amounts) != 1 or extracted.amount_text != amounts[0]:
        warnings.append("A single explicit USD amount could not be established; review missing or conflicting amounts.")
    elif re.search(r"€|£|\b(?:EUR|GBP|CAD|AUD|Canadian|Australian)\b|(?:CA|AU)\$", text, re.I):
        warnings.append("Only USD is supported; currency is unsupported or ambiguous.")
    else:
        amount = int(Decimal(re.sub(r"USD|[$,\s]", "", amounts[0], flags=re.I)) * 100)
        if amount <= 0 or amount > 100_000_000_00:
            warnings.append("Amount is outside the supported positive demo range (up to $100 million).")
            amount = None
    if extracted.claimed_sender is None:
        warnings.append("Claimed sender name is missing or ambiguous.")
    if extracted.vendor is None:
        warnings.append("Vendor is missing, unrecognized by offline parsing, or ambiguous.")
    if len(re.findall(r"\bDEMO-ACCOUNT-\d{4}\b", text)) > 1:
        warnings.append("Multiple payment-account references require manual review.")
    if INJECTION.search(text):
        warnings.append("Possible instructions aimed at manipulating the investigation were detected.")
    # Negative signals are a union of AI interpretation and transparent phrase rules.
    extracted = extracted.model_copy(update={
        "urgency_quotes": list(dict.fromkeys(extracted.urgency_quotes + [m.group() for m in URGENCY.finditer(text)])),
        "secrecy_quotes": list(dict.fromkeys(extracted.secrecy_quotes + [m.group() for m in SECRECY.finditer(text)])),
    })
    return ParsedRequest(extracted, amount, warnings)
