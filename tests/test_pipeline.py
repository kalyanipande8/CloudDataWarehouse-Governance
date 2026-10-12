import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.schema import build_warehouse
from src.query_optimization import compare_query_performance
from src.governance import audit_readiness_check, hipaa_sensitive_columns


@pytest.fixture(scope="module")
def conn():
    return build_warehouse()


def test_warehouse_has_fact_and_dimension_tables(conn):
    cur = conn.cursor()
    for table in ["fact_claims", "dim_patient", "dim_provider"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        assert cur.fetchone()[0] > 0


def test_optimized_query_is_faster_than_naive(conn):
    result = compare_query_performance(conn)
    assert result["optimized_query_mean_sec"] < result["naive_query_mean_sec"]
    assert result["latency_reduction_pct"] > 0


def test_both_queries_return_identical_results(conn):
    cur = conn.cursor()
    from src.query_optimization import NAIVE_QUERY, OPTIMIZED_QUERY
    cur.execute(NAIVE_QUERY)
    naive_results = sorted(cur.fetchall())
    cur.execute(OPTIMIZED_QUERY)
    optimized_results = sorted(cur.fetchall())
    assert len(naive_results) == len(optimized_results)
    for (s1, a1), (s2, a2) in zip(naive_results, optimized_results):
        assert s1 == s2
        assert abs(a1 - a2) < 0.01


def test_audit_readiness_is_fully_verified():
    result = audit_readiness_check()
    assert result["pct_audit_ready"] == 100.0
    assert result["missing"] == []


def test_hipaa_sensitive_columns_identified():
    sensitive = hipaa_sensitive_columns()
    assert len(sensitive) > 0
    assert "dim_patient.patient_id" in sensitive
