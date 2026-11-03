"""Single source of truth for fictional company policy configuration.

Phase 1 displays these policies; enforcement arrives in Phase 3.
Money is represented as integer cents to avoid floating-point rounding.
"""

ADDITIONAL_APPROVAL_THRESHOLD_CENTS = 5_000_000
POLICIES = (
    ("P01", f"Payments over ${ADDITIONAL_APPROVAL_THRESHOLD_CENTS / 100:,.0f} require additional approval."),
    ("P02", "Vendor bank-account changes require independent verification."),
    ("P03", "Unrecognized senders must be flagged for review."),
    ("P04", "Secrecy or extreme urgency requires analyst review."),
    ("P05", "A requester must have sufficient payment approval authority."),
    ("P06", "A human analyst makes the final decision; Verity never executes a payment."),
)
