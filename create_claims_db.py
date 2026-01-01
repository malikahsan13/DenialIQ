import sqlite3
import random

# Connect to SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect("claims.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_number TEXT,
    patient_name TEXT,
    cpt_code TEXT,
    status TEXT,
    amount REAL
)
""")

# Insert initial records
initial_claims = [
    ('CLM-1001', 'John Doe', '99213', 'DENIED', 125.0),
    ('CLM-1002', 'Jane Smith', '99214', 'PAID', 210.0)
]

cursor.executemany("INSERT INTO claims (claim_number, patient_name, cpt_code, status, amount) VALUES (?, ?, ?, ?, ?)", initial_claims)

# Generate more sample claims
first_names = ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 'Grace', 'Helen', 'Ian', 'Jack', 'Kelly', 'Liam', 'Mia', 'Noah', 'Olivia', 'Paul', 'Quinn', 'Rachel', 'Steve', 'Tina']
last_names = ['Anderson', 'Brown', 'Clark', 'Davis', 'Evans', 'Franklin', 'Garcia', 'Harris', 'Ibrahim', 'Jones', 'Khan', 'Lewis', 'Martinez', 'Nelson', 'Olsen', 'Patel', 'Quincy', 'Roberts', 'Smith', 'Turner']
cpt_codes = ['99213', '99214', '99215', '99385', '99386', '99203', '99204', '99205']
statuses = ['PAID', 'DENIED', 'PENDING']

for i in range(100):
    claim_number = f"CLM-{1003 + i}"
    patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    cpt_code = random.choice(cpt_codes)
    status = random.choice(statuses)
    amount = round(random.uniform(50, 1000), 2)  # amount between 50 and 1000
    cursor.execute("INSERT INTO claims (claim_number, patient_name, cpt_code, status, amount) VALUES (?, ?, ?, ?, ?)",
                   (claim_number, patient_name, cpt_code, status, amount))

# Commit changes and close connection
conn.commit()
conn.close()

print("SQLite DB 'claims.db' created with 102 sample claims!")
