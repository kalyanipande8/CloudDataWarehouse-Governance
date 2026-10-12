"""End-to-end: build the star-schema warehouse, compare naive vs.
optimized query performance, and check governance/audit readiness."""
import json
import os

from src.schema import build_warehouse
from src.query_optimization import compare_query_performance
from src.governance import audit_readiness_check, hipaa_sensitive_columns

os.makedirs("results", exist_ok=True)

print("=== Building star-schema warehouse (SQLite stand-in for a cloud warehouse) ===")
conn = build_warehouse()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM fact_claims")
print("fact_claims rows:", cur.fetchone()[0])

print("\n=== Query performance: naive correlated subquery vs. optimized indexed JOIN ===")
performance = compare_query_performance(conn)
print(performance)

print("\n=== Governance & audit readiness ===")
audit = audit_readiness_check()
print(audit)
sensitive = hipaa_sensitive_columns()
print("HIPAA-sensitive columns:", sensitive)

summary = {
    "naive_query_mean_sec": performance["naive_query_mean_sec"],
    "optimized_query_mean_sec": performance["optimized_query_mean_sec"],
    "latency_reduction_pct": performance["latency_reduction_pct"],
    "pct_audit_ready": audit["pct_audit_ready"],
    "n_hipaa_sensitive_columns": len(sensitive),
}
with open("results/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n=== Summary ===")
print(json.dumps(summary, indent=2))
