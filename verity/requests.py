"""Request-entry validation only; no AI parsing or risk analysis in Phase 1."""

MAX_REQUEST_LENGTH = 10000
SAMPLES = {
    "Routine vendor payment": "From: elena.brooks@northwind.example\nSubject: Cedar invoice 1042\n\nPlease schedule a $1,525 payment to Cedar Office Supply using the existing account on file. Invoice 1042 covers this month's office supplies.\n\nElena Brooks, AP Manager",
    "Executive impersonation": "From: jim.carter@northwind-finance.example\nSubject: Urgent wire transfer\n\nPlease transfer $480,000 to our new supplier today. This is confidential, so do not discuss it with anyone. I'm in meetings all day, so email only.\n\nJim Carter, CFO",
    "Vendor account change": "From: liam.chen@northwind.example\nSubject: Silverline equipment invoice\n\nPlease arrange $27,500 for Silverline Equipment. Their bank account changed recently. Confirm the new details independently before processing.\n\nLiam Chen, Treasury Manager",
}


def validate_request(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter a payment request before previewing it.")
    if len(text) > MAX_REQUEST_LENGTH:
        raise ValueError(f"Requests must contain at most {MAX_REQUEST_LENGTH:,} characters.")
    return text.strip()
