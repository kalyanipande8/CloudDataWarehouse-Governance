"""A real star-schema cloud data warehouse, built in SQLite as a local,
honestly-disclosed stand-in for a cloud warehouse (Snowflake/Redshift/
Synapse) -- the schema design and SQL are genuine, only the hosting
engine differs."""
from __future__ import annotations

import sqlite3

import numpy as np

N_PATIENTS = 1500
N_PROVIDERS = 100
N_CLAIMS = 8_000
SEED = 163


def build_warehouse(db_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE dim_patient (
            patient_key INTEGER PRIMARY KEY, patient_id TEXT, state TEXT, age_band TEXT
        );
        CREATE TABLE dim_provider (
            provider_key INTEGER PRIMARY KEY, provider_id TEXT, specialty TEXT
        );
        CREATE TABLE fact_claims (
            claim_key INTEGER PRIMARY KEY, patient_key INTEGER, provider_key INTEGER,
            claim_amount REAL, claim_date TEXT,
            FOREIGN KEY (patient_key) REFERENCES dim_patient(patient_key),
            FOREIGN KEY (provider_key) REFERENCES dim_provider(provider_key)
        );
    """)

    rng = np.random.default_rng(SEED)
    states = ["NY", "CA", "TX", "FL", "IL"]
    age_bands = ["18-34", "35-54", "55-74", "75+"]
    specialties = ["Cardiology", "Primary Care", "Oncology", "Orthopedics"]

    patients = [(i, f"PAT-{i:05d}", rng.choice(states), rng.choice(age_bands)) for i in range(N_PATIENTS)]
    providers = [(i, f"PROV-{i:04d}", rng.choice(specialties)) for i in range(N_PROVIDERS)]
    claims = [
        (i, int(rng.integers(0, N_PATIENTS)), int(rng.integers(0, N_PROVIDERS)),
         round(float(rng.gamma(2, 100)), 2), f"2025-{int(rng.integers(1,13)):02d}-{int(rng.integers(1,28)):02d}")
        for i in range(N_CLAIMS)
    ]

    cur.executemany("INSERT INTO dim_patient VALUES (?,?,?,?)", patients)
    cur.executemany("INSERT INTO dim_provider VALUES (?,?,?)", providers)
    cur.executemany("INSERT INTO fact_claims VALUES (?,?,?,?,?)", claims)
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = build_warehouse()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fact_claims")
    print("fact_claims rows:", cur.fetchone()[0])
