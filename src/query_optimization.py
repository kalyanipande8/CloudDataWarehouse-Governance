"""Real, measured query-latency comparison: a naive correlated-subquery
version of a common analytics query vs. an optimized indexed-JOIN
version -- both run against the actual SQLite warehouse, timed over
multiple repeats for a stable measurement."""
from __future__ import annotations

import time

NAIVE_QUERY = """
SELECT p.state,
       (SELECT AVG(f.claim_amount) FROM fact_claims f
        WHERE f.patient_key IN (SELECT patient_key FROM dim_patient WHERE state = p.state)) AS avg_claim
FROM dim_patient p
GROUP BY p.state;
"""

OPTIMIZED_QUERY = """
SELECT p.state, AVG(f.claim_amount) AS avg_claim
FROM fact_claims f
JOIN dim_patient p ON f.patient_key = p.patient_key
GROUP BY p.state;
"""


def add_indexes(conn) -> None:
    cur = conn.cursor()
    cur.execute("CREATE INDEX idx_fact_patient ON fact_claims(patient_key)")
    cur.execute("CREATE INDEX idx_dim_patient_state ON dim_patient(state)")
    conn.commit()


def time_query(conn, query: str, n_repeats: int = 5) -> float:
    cur = conn.cursor()
    times = []
    for _ in range(n_repeats):
        start = time.perf_counter()
        cur.execute(query)
        cur.fetchall()
        times.append(time.perf_counter() - start)
    return sum(times) / len(times)


def compare_query_performance(conn) -> dict:
    naive_time = time_query(conn, NAIVE_QUERY)
    add_indexes(conn)
    optimized_time = time_query(conn, OPTIMIZED_QUERY)

    improvement_pct = round(100 * (1 - optimized_time / naive_time), 2)
    return {
        "naive_query_mean_sec": round(naive_time, 5),
        "optimized_query_mean_sec": round(optimized_time, 5),
        "latency_reduction_pct": improvement_pct,
    }


if __name__ == "__main__":
    from .schema import build_warehouse

    conn = build_warehouse()
    print(compare_query_performance(conn))
