import sqlite3
import random
from datetime import datetime, timedelta

# Connect to SQLite
conn = sqlite3.connect("claims.db")
cursor = conn.cursor()

# 1️⃣ Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS claims (
    claim_number TEXT,
    patient_name TEXT,
    cpt_code TEXT,
    status TEXT,
    billed_amount REAL,
    allowed_amount REAL,
    denied_amount REAL,
    denial_code TEXT,
    adjustment_code TEXT,
    adjustment_amount REAL,
    patient_responsibility REAL,
    payer_name TEXT,
    service_date TEXT
)
""")

# 2️⃣ Sample data
cpt_codes = ["99213", "99214", "99215", "93000", "71020", "80050", "36415", "99385", "99386"]
denial_codes = ["M115", "M116", "M117", "M126", "M10", "M11", "M12", "M13", "M17", None]       # Only M/N codes
adjustment_codes = ["Co-45", "CO-1", "CO-5", "CO-15", None]
payers = ["Aetna", "United Healthcare", "BCBS", "Cigna", "Medicare"]
statuses = ["PAID", "DENIED", "PARTIAL"]
first_names = ["John", "Jane", "Ali", "Sara", "Michael", "Fatima", "David", "Ayesha"]
last_names = ["Smith", "Khan", "Ahmed", "Brown", "Patel", "Garcia", "Lee"]
start_date = datetime(2024, 1, 1)

def random_date():
    return (start_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")

# 3️⃣ Generate 150 claims
records = []

for i in range(150):
    claim_number = f"CLM-{5000 + i}"  # Start from 5000 to avoid conflict
    patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    cpt_code = random.choice(cpt_codes)
    status = random.choice(statuses)

    billed = round(random.uniform(80, 1200), 2)

    if status == "PAID":
        allowed = billed
        denied = 0.0
        denial_code = None
    elif status == "DENIED":
        allowed = 0.0
        denied = billed
        denial_code = random.choice(["M115", "M116", "M117", "M126", "M10", "M11", "M12", "M13", "M17"])
    else:  # PARTIAL
        allowed = round(billed * random.uniform(0.3, 0.8), 2)
        denied = round(billed - allowed, 2)
        denial_code = random.choice(["M115", "M116", "M117", "M126", "M10", "M11", "M12", "M13", "M17"])

    adjustment_code = random.choice(adjustment_codes)
    adjustment_amount = round(denied * random.uniform(0.2, 1.0), 2) if denied > 0 else 0.0
    patient_resp = round(billed - allowed, 2) if status != "PAID" else 0.0

    payer = random.choice(payers)
    service_date = random_date()

    records.append((
        claim_number,
        patient_name,
        cpt_code,
        status,
        billed,
        allowed,
        denied,
        denial_code,
        adjustment_code,
        adjustment_amount,
        patient_resp,
        payer,
        service_date
    ))

# 4️⃣ Insert into SQLite
cursor.executemany("""
INSERT INTO claims (
    claim_number,
    patient_name,
    cpt_code,
    status,
    billed_amount,
    allowed_amount,
    denied_amount,
    denial_code,
    adjustment_code,
    adjustment_amount,
    patient_responsibility,
    payer_name,
    service_date
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", records)

conn.commit()
conn.close()

print("✅ 150 claim records with M/N codes inserted successfully.")
