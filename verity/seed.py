"""Reproducible synthetic records. All names, contacts, and accounts are fictional."""

from datetime import date, timedelta


def employees() -> list[tuple]:
    staff = [
        ("Jim Carter", "Chief Financial Officer", "Finance", 500000),
        ("Maya Bennett", "Controller", "Finance", 100000),
        ("Elena Brooks", "AP Manager", "Finance", 50000),
        ("Noah Patel", "AP Analyst", "Finance", 10000),
        ("Ava Reed", "AP Analyst", "Finance", 10000),
        ("Liam Chen", "Treasury Manager", "Finance", 75000),
        ("Sofia Hayes", "Treasury Analyst", "Finance", 15000),
        ("Ethan Ross", "Procurement Director", "Operations", 50000),
        ("Isla Morgan", "Buyer", "Operations", 10000),
        ("Oliver Grant", "Operations Director", "Operations", 50000),
        ("Amelia Park", "HR Director", "People", 25000),
        ("Lucas Flynn", "HR Specialist", "People", 0),
        ("Mia Stone", "IT Director", "Technology", 40000),
        ("Henry Cole", "Systems Analyst", "Technology", 0),
        ("Charlotte Lane", "Security Manager", "Technology", 10000),
        ("James Ellis", "Sales Director", "Sales", 25000),
        ("Harper Wells", "Account Executive", "Sales", 0),
        ("Benjamin Scott", "Marketing Director", "Marketing", 25000),
        ("Evelyn Shaw", "Legal Counsel", "Legal", 25000),
        ("Daniel Rivera", "Chief Executive Officer", "Executive", 500000),
    ]
    return [
        (f"E{i:03}", name, title, dept,
         f"{name.lower().replace(' ', '.')}@northwind.example",
         f"+1-202-555-{100+i:04}", authority * 100)
        for i, (name, title, dept, authority) in enumerate(staff, 1)
    ]


def vendors() -> list[tuple]:
    names = ["Cedar Office Supply", "Summit Cloud Services", "Harbor Logistics",
             "Maple Industrial Parts", "Cobalt Consulting", "Willow Facilities",
             "Juniper Packaging", "Beacon Telecom", "Aspen Training",
             "Silverline Equipment", "Meadow Catering", "Pinecrest Software",
             "Orchard Printworks", "Granite Safety", "Brookside Analytics"]
    return [
        (f"V{i:03}", name, f"DEMO-ACCOUNT-{i:04}",
         "Monthly" if i % 3 else "Quarterly",
         "2026-10-30" if i == 10 else "2025-06-15",
         "Suspended" if i == 14 else "Active")
        for i, name in enumerate(names, 1)
    ]


def transactions() -> list[tuple]:
    rows = []
    for i in range(1, 101):
        vendor_number = (i - 1) % 15 + 1
        amount = (1200 + vendor_number * 325 + (i % 5) * 110) * 100
        rows.append((f"PAY{i:04}", ["E003", "E004", "E005", "E006"][i % 4],
                     f"V{vendor_number:03}", amount,
                     (date(2026, 3, 1) + timedelta(days=i * 2)).isoformat(),
                     "Cancelled" if i % 17 == 0 else "Paid"))
    return rows
