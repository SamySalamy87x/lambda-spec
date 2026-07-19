"""Product-grade analysis utilities for λ-SPEC Resilience Lab.

The functions in this module keep the mathematical core small and auditable while
adding the workflow a real user needs: input validation, rolling measurements,
environment-withdrawal stress testing, driver ranking, and exportable reports.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import numpy as np

from lambda_spec.core import coupling, dlambda_dt

_ALLOWED_METHODS = {"spearman", "pearson", "residual"}


def _as_2d(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.ndim != 2:
        raise ValueError("Expected a one- or two-dimensional numeric array")
    return arr


def _state(phi_value: float) -> str:
    if phi_value < 0.35:
        return "robust"
    if phi_value < 0.60:
        return "watch"
    return "fragile"


def _trend(slope: float) -> str:
    if slope > 0.002:
        return "strengthening"
    if slope < -0.002:
        return "weakening"
    return "stable"


def clean_numeric_rows(columns: Sequence[str], rows: Sequence[Sequence[Any]], selected: Sequence[str]) -> tuple[np.ndarray, list[int]]:
    """Extract selected columns and drop rows with non-numeric/missing values."""
    if not columns:
        raise ValueError("No columns were provided")
    if len(set(columns)) != len(columns):
        raise ValueError("Column names must be unique")
    if not selected:
        raise ValueError("Select at least one column")
    index = {name: i for i, name in enumerate(columns)}
    missing = [name for name in selected if name not in index]
    if missing:
        raise ValueError(f"Unknown columns: {', '.join(missing)}")
    clean: list[list[float]] = []
    kept: list[int] = []
    for row_index, row in enumerate(rows):
        if len(row) < len(columns):
            continue
        converted: list[float] = []
        valid = True
        for name in selected:
            try:
                number = float(row[index[name]])
            except (TypeError, ValueError):
                valid = False
                break
            if not np.isfinite(number):
                valid = False
                break
            converted.append(number)
        if valid:
            clean.append(converted)
            kept.append(row_index)
    if len(clean) < 3:
        raise ValueError("At least 3 complete numeric rows are required")
    return np.asarray(clean, dtype=float), kept


def rolling_coupling(x: np.ndarray, env: np.ndarray, *, method: str = "spearman", window: int | None = None) -> list[dict[str, float | int]]:
    """Measure λ and Φ across overlapping windows."""
    x = _as_2d(x)
    env = _as_2d(env)
    n = x.shape[0]
    if n != env.shape[0]:
        raise ValueError("System and environment arrays must have the same rows")
    if window is None:
        window = max(8, min(n, int(round(n / 5))))
    window = int(window)
    if window < 3 or window > n:
        raise ValueError(f"Window must be between 3 and {n}")
    step = max(1, window // 10)
    starts = list(range(0, n - window + 1, step))
    final_start = n - window
    if not starts or starts[-1] != final_start:
        starts.append(final_start)
    output: list[dict[str, float | int]] = []
    for start in starts:
        end = start + window
        result = coupling(x[start:end], env[start:end], method=method)
        output.append({"start": int(start), "end": int(end - 1), "center": float(start + (window - 1) / 2), "lambda": float(result.lam), "phi": float(result.phi)})
    return output


def withdrawal_curve(x: np.ndarray, env: np.ndarray, *, method: str = "spearman", steps: int = 11, seed: int = 47) -> list[dict[str, float]]:
    """Estimate the coupling envelope as environmental signal is withdrawn."""
    x = _as_2d(x)
    env = _as_2d(env)
    if steps < 3 or steps > 101:
        raise ValueError("steps must be between 3 and 101")
    rng = np.random.default_rng(seed)
    permuted = np.empty_like(env)
    for col in range(env.shape[1]):
        permuted[:, col] = env[rng.permutation(env.shape[0]), col]
    fractions = np.linspace(0.0, 1.0, steps)
    raw_lambdas = [coupling(x, (1.0 - fraction) * env + fraction * permuted, method=method).lam for fraction in fractions]
    envelope = np.minimum.accumulate(np.asarray(raw_lambdas, dtype=float))
    return [{"withdrawal": float(fraction), "lambda": float(lam), "phi": float(1.0 - lam), "raw_lambda": float(raw)} for fraction, lam, raw in zip(fractions, envelope, raw_lambdas)]


def rank_environment_drivers(x: np.ndarray, env: np.ndarray, names: Sequence[str], *, method: str = "spearman") -> list[dict[str, float | str]]:
    """Rank environmental columns by drop-one loss of λ."""
    x = _as_2d(x)
    env = _as_2d(env)
    if len(names) != env.shape[1]:
        raise ValueError("Environment names do not match environment columns")
    baseline = coupling(x, env, method=method).lam
    raw: list[float] = []
    for col in range(env.shape[1]):
        score = baseline if env.shape[1] == 1 else max(0.0, baseline - coupling(x, np.delete(env, col, axis=1), method=method).lam)
        raw.append(float(score))
    total = float(sum(raw))
    normalized = [0.0 for _ in raw] if total <= 1e-12 else [value / total for value in raw]
    ranked = [{"name": name, "importance": float(weight), "lambda_loss": float(loss)} for name, weight, loss in zip(names, normalized, raw)]
    ranked.sort(key=lambda item: (item["importance"], item["lambda_loss"]), reverse=True)
    return ranked


def analyze_resilience(x: Any, env: Any, *, system_names: Sequence[str] | None = None, environment_names: Sequence[str] | None = None, method: str = "spearman", window: int | None = None, title: str = "Untitled system", source: str = "user data") -> dict[str, Any]:
    """Run the full λ-SPEC Resilience Lab analysis."""
    if method not in _ALLOWED_METHODS:
        raise ValueError(f"Method must be one of: {', '.join(sorted(_ALLOWED_METHODS))}")
    x = _as_2d(x)
    env = _as_2d(env)
    if x.shape[0] != env.shape[0]:
        raise ValueError("System and environment arrays must have the same rows")
    if x.shape[0] < 3:
        raise ValueError("At least 3 rows are required")
    system_names = list(system_names or [f"system_{i + 1}" for i in range(x.shape[1])])
    environment_names = list(environment_names or [f"environment_{i + 1}" for i in range(env.shape[1])])
    if len(system_names) != x.shape[1]:
        raise ValueError("System names do not match system columns")
    if len(environment_names) != env.shape[1]:
        raise ValueError("Environment names do not match environment columns")
    base = coupling(x, env, method=method)
    rolling = rolling_coupling(x, env, method=method, window=window)
    lambda_series = np.asarray([point["lambda"] for point in rolling], dtype=float)
    slope = dlambda_dt(lambda_series) if len(lambda_series) >= 2 else 0.0
    stress = withdrawal_curve(x, env, method=method)
    drivers = rank_environment_drivers(x, env, environment_names, method=method)
    rolling_std = float(np.std(lambda_series)) if len(lambda_series) > 1 else 0.0
    sample_factor = min(1.0, np.log10(max(10, x.shape[0])) / 3.0)
    stability_factor = max(0.0, 1.0 - min(1.0, rolling_std * 2.0))
    confidence_score = float(np.clip(0.35 + 0.45 * sample_factor + 0.20 * stability_factor, 0.0, 1.0))
    confidence_label = "high" if confidence_score >= 0.80 else "moderate" if confidence_score >= 0.60 else "limited"
    top_driver = drivers[0]["name"] if drivers and drivers[0]["importance"] > 0 else None
    state = _state(base.phi)
    trend = _trend(slope)
    summary = {"headline": f"{state.title()} coupling profile; trajectory is {trend}.", "evidence": [f"Global λ = {base.lam:.3f} and Φ = {base.phi:.3f} using {method} coupling.", f"Rolling λ slope = {slope:+.4f} across {len(rolling)} analysis windows.", f"Most influential measured environmental driver: {top_driver}." if top_driver else "No single measured environmental driver dominated the drop-one analysis."], "limits": ["Coupling is association, not proof of causation.", "Unmeasured environmental variables can change the result.", "The withdrawal simulation is a stress-test envelope, not a literal forecast."]}
    return {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "title": title, "source": source, "method": method, "sample_count": int(x.shape[0]), "system_variables": system_names, "environment_variables": environment_names, "global": {**asdict(base), "state": state}, "trajectory": {"lambda_slope": float(slope), "trend": trend, "rolling_std": rolling_std, "window": int(rolling[0]["end"] - rolling[0]["start"] + 1), "points": rolling}, "withdrawal": stress, "drivers": drivers, "confidence": {"score": confidence_score, "label": confidence_label}, "summary": summary}


def analyze_table(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze a browser/API table payload."""
    columns = list(payload.get("columns") or [])
    rows = list(payload.get("rows") or [])
    system_columns = list(payload.get("system_columns") or [])
    environment_columns = list(payload.get("environment_columns") or [])
    overlap = set(system_columns) & set(environment_columns)
    if overlap:
        raise ValueError(f"Columns cannot be both system and environment: {', '.join(sorted(overlap))}")
    selected = system_columns + environment_columns
    matrix, kept = clean_numeric_rows(columns, rows, selected)
    split = len(system_columns)
    result = analyze_resilience(matrix[:, :split], matrix[:, split:], system_names=system_columns, environment_names=environment_columns, method=str(payload.get("method") or "spearman"), window=payload.get("window"), title=str(payload.get("title") or "Untitled system"), source=str(payload.get("source") or "uploaded table"))
    result["data_quality"] = {"input_rows": len(rows), "used_rows": len(kept), "dropped_rows": len(rows) - len(kept), "kept_row_indices": kept}
    return result


def markdown_report(result: Mapping[str, Any], narrative: str | None = None) -> str:
    """Create an auditable Markdown report from an analysis result."""
    global_result = result["global"]
    trajectory = result["trajectory"]
    confidence = result["confidence"]
    drivers = result.get("drivers", [])
    lines = [f"# λ-SPEC Resilience Report — {result.get('title', 'Untitled system')}", "", f"Generated: {result.get('generated_at', '')}", f"Source: {result.get('source', '')}", f"Method: `{result.get('method', '')}`", f"Samples: {result.get('sample_count', '')}", "", "## Decision snapshot", "", f"- **λ (coupling):** {global_result['lam']:.4f}", f"- **Φ (fragility):** {global_result['phi']:.4f}", f"- **State:** {global_result['state']}", f"- **Trajectory:** {trajectory['trend']} ({trajectory['lambda_slope']:+.5f} λ/window)", f"- **Confidence:** {confidence['label']} ({confidence['score']:.0%})", "", "## Environmental drivers", "", "| Rank | Driver | Relative importance | λ loss when removed |", "|---:|---|---:|---:|"]
    for rank, item in enumerate(drivers, start=1):
        lines.append(f"| {rank} | {item['name']} | {item['importance']:.1%} | {item['lambda_loss']:.4f} |")
    if not drivers:
        lines.append("| — | No drivers available | — | — |")
    lines.extend(["", "## Evidence", ""])
    lines.extend(f"- {item}" for item in result["summary"]["evidence"])
    if narrative:
        lines.extend(["", "## GPT-assisted interpretation", "", narrative.strip()])
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in result["summary"]["limits"])
    lines.extend(["", "---", "This report measures observed coupling. It does not establish causal, clinical, financial, or safety certification."])
    return "\n".join(lines) + "\n"
