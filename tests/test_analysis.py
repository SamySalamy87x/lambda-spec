import numpy as np
import pytest
from lambda_spec import synthetic
from lambda_spec.analysis import analyze_resilience, analyze_table, clean_numeric_rows, markdown_report, withdrawal_curve


def test_full_analysis_is_json_ready():
    x, env = synthetic.telemetry_subsystems(n=180)
    result = analyze_resilience(x, env, system_names=["power", "thermal", "comms"], environment_names=["orbital", "phase"], window=36, title="Telemetry")
    assert 0 <= result["global"]["lam"] <= 1
    assert 0 <= result["global"]["phi"] <= 1
    assert len(result["trajectory"]["points"]) >= 2
    assert len(result["withdrawal"]) == 11
    assert result["drivers"][0]["name"] in {"orbital", "phase"}
    assert result["confidence"]["label"] in {"limited", "moderate", "high"}


def test_withdrawal_envelope_is_monotone():
    x, env = synthetic.bistable_switch(n=200)
    curve = withdrawal_curve(x, env)
    lambdas = np.array([point["lambda"] for point in curve])
    assert np.all(np.diff(lambdas) <= 1e-12)


def test_table_cleaning_reports_drops():
    payload = {"columns": ["system", "environment", "note"], "rows": [[1, 1, "a"], [2, 2, "b"], [3, "bad", "c"], [4, 4, "d"], [5, 5, "e"]], "system_columns": ["system"], "environment_columns": ["environment"], "window": 3}
    result = analyze_table(payload)
    assert result["data_quality"]["input_rows"] == 5
    assert result["data_quality"]["used_rows"] == 4
    assert result["data_quality"]["dropped_rows"] == 1


def test_overlap_is_rejected():
    with pytest.raises(ValueError, match="both system and environment"):
        analyze_table({"columns": ["a", "b"], "rows": [[1, 1], [2, 2], [3, 3]], "system_columns": ["a"], "environment_columns": ["a"]})


def test_markdown_report_contains_audit_sections():
    x, env = synthetic.isolated_system(n=80)
    result = analyze_resilience(x, env, window=16, title="Control")
    report = markdown_report(result, "Bounded narrative.")
    assert "# λ-SPEC Resilience Report" in report
    assert "## Evidence" in report
    assert "## Limits" in report
    assert "Bounded narrative." in report


def test_clean_numeric_rows_requires_complete_data():
    with pytest.raises(ValueError, match="At least 3"):
        clean_numeric_rows(["a"], [[1], ["bad"]], ["a"])
