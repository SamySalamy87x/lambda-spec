"""Zero-framework web application for λ-SPEC Resilience Lab.

Run with:
    python -m lambda_spec.webapp
or after installation:
    lambda-spec-lab
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import numpy as np

from lambda_spec import synthetic
from lambda_spec.analysis import analyze_table, markdown_report

STATIC_DIR = Path(__file__).with_name("static")
MAX_BODY_BYTES = 5 * 1024 * 1024


def _round_rows(matrix: np.ndarray, digits: int = 6) -> list[list[float]]:
    return np.round(np.asarray(matrix, dtype=float), digits).tolist()


def _demo_telemetry() -> dict[str, Any]:
    x, env = synthetic.telemetry_subsystems(n=240, seed=12)
    t = np.arange(len(x), dtype=float)
    data = np.column_stack([t, x, env])
    return {
        "title": "Orbital telemetry coupling",
        "source": "λ-SPEC synthetic telemetry demo",
        "columns": ["time", "power", "thermal", "comms", "orbital_cycle", "solar_phase"],
        "rows": _round_rows(data),
        "system_columns": ["power", "thermal", "comms"],
        "environment_columns": ["orbital_cycle", "solar_phase"],
        "method": "spearman",
        "window": 48,
    }


def _demo_degradation() -> dict[str, Any]:
    rng = np.random.default_rng(22)
    n = 260
    t = np.arange(n, dtype=float)
    driver = np.sin(np.linspace(0, 14 * np.pi, n))
    support = np.cos(np.linspace(0, 5 * np.pi, n))
    strength = np.linspace(0.95, 0.15, n)
    service = strength * driver + 0.25 * support + rng.normal(0, 0.18, n)
    latency = -0.75 * strength * driver + rng.normal(0, 0.22, n)
    quality = 0.65 * strength * driver + 0.20 * support + rng.normal(0, 0.20, n)
    data = np.column_stack([t, service, latency, quality, driver, support, strength])
    return {
        "title": "Network support withdrawal",
        "source": "λ-SPEC progressive-decoupling demo",
        "columns": ["time", "service_output", "latency_inverse", "quality", "demand_cycle", "backup_support", "hidden_strength"],
        "rows": _round_rows(data),
        "system_columns": ["service_output", "latency_inverse", "quality"],
        "environment_columns": ["demand_cycle", "backup_support"],
        "method": "spearman",
        "window": 50,
    }


def _demo_supply_chain() -> dict[str, Any]:
    rng = np.random.default_rng(5)
    n = 180
    t = np.arange(n, dtype=float)
    demand = 100 + 20 * np.sin(t / 9) + rng.normal(0, 5, n)
    supplier_fill = np.clip(0.92 + 0.04 * np.sin(t / 17) + rng.normal(0, 0.025, n), 0.65, 1.0)
    transport = np.clip(0.88 + 0.05 * np.cos(t / 13) + rng.normal(0, 0.03, n), 0.60, 1.0)
    inventory = 0.55 * demand * supplier_fill + 28 * transport + rng.normal(0, 4, n)
    fulfilled = demand * supplier_fill * transport + rng.normal(0, 4, n)
    backlog = demand - fulfilled + rng.normal(0, 2, n)
    data = np.column_stack([t, inventory, fulfilled, backlog, demand, supplier_fill, transport])
    return {
        "title": "Supply-chain resilience",
        "source": "λ-SPEC operations demo",
        "columns": ["time", "inventory", "fulfilled_orders", "backlog", "demand", "supplier_fill", "transport_reliability"],
        "rows": _round_rows(data),
        "system_columns": ["inventory", "fulfilled_orders", "backlog"],
        "environment_columns": ["demand", "supplier_fill", "transport_reliability"],
        "method": "spearman",
        "window": 36,
    }


def _demo_isolated() -> dict[str, Any]:
    x, env = synthetic.isolated_system(n=160, seed=9)
    t = np.arange(len(x), dtype=float)
    data = np.column_stack([t, x, env])
    return {
        "title": "Isolated-system control",
        "source": "λ-SPEC negative control",
        "columns": ["time", "system_output", "environment_a", "environment_b"],
        "rows": _round_rows(data),
        "system_columns": ["system_output"],
        "environment_columns": ["environment_a", "environment_b"],
        "method": "spearman",
        "window": 32,
    }


DEMO_FACTORIES = {
    "telemetry": _demo_telemetry,
    "degradation": _demo_degradation,
    "supply-chain": _demo_supply_chain,
    "isolated": _demo_isolated,
}


def _safe_result_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    drivers = result.get("drivers", [])[:5]
    return {
        "title": result.get("title"),
        "method": result.get("method"),
        "sample_count": result.get("sample_count"),
        "system_variables": result.get("system_variables"),
        "environment_variables": result.get("environment_variables"),
        "global": result.get("global"),
        "trajectory": {
            key: result.get("trajectory", {}).get(key)
            for key in ["lambda_slope", "trend", "rolling_std", "window"]
        },
        "drivers": drivers,
        "confidence": result.get("confidence"),
        "summary": result.get("summary"),
    }


def _fallback_narrative(result: dict[str, Any], lang: str = "en") -> str:
    global_result = result.get("global", {})
    trajectory = result.get("trajectory", {})
    confidence = result.get("confidence", {})
    drivers = result.get("drivers", [])
    top = drivers[0] if drivers else None
    if lang == "es":
        driver_text = (
            f"El impulsor ambiental medido con mayor pérdida de λ al retirarlo es **{top['name']}** "
            f"(pérdida {top['lambda_loss']:.3f})."
            if top and top.get("lambda_loss", 0) > 0
            else "El análisis no identifica un impulsor ambiental dominante con los datos disponibles."
        )
        return (
            f"El sistema presenta **λ={global_result.get('lam', 0):.3f}** y "
            f"**Φ={global_result.get('phi', 0):.3f}**, clasificado como **{global_result.get('state', 'sin clasificar')}**. "
            f"La trayectoria es **{trajectory.get('trend', 'estable')}** con pendiente "
            f"{trajectory.get('lambda_slope', 0):+.4f} por ventana. {driver_text} "
            f"La confianza analítica es **{confidence.get('label', 'limitada')}**. "
            "Esto mide asociación estructural y sensibilidad al retiro del entorno; no demuestra causalidad ni constituye una predicción literal."
        )
    driver_text = (
        f"The measured environmental driver with the largest drop-one λ loss is **{top['name']}** "
        f"(loss {top['lambda_loss']:.3f})."
        if top and top.get("lambda_loss", 0) > 0
        else "No single measured environmental driver dominates the available data."
    )
    return (
        f"The system has **λ={global_result.get('lam', 0):.3f}** and "
        f"**Φ={global_result.get('phi', 0):.3f}**, classified as **{global_result.get('state', 'unclassified')}**. "
        f"Its trajectory is **{trajectory.get('trend', 'stable')}** with a λ slope of "
        f"{trajectory.get('lambda_slope', 0):+.4f} per window. {driver_text} "
        f"Analytical confidence is **{confidence.get('label', 'limited')}**. "
        "This is an association and withdrawal-sensitivity measurement; it does not prove causation or provide a literal forecast."
    )


def _openai_narrative(result: dict[str, Any], question: str, lang: str) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_narrative(result, lang), "deterministic"
    try:
        from openai import OpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-5.6")
        client = OpenAI(api_key=api_key, timeout=30.0)
        snapshot = _safe_result_snapshot(result)
        language = "Spanish" if lang == "es" else "English"
        prompt = (
            "You are the evidence interpreter inside λ-SPEC Resilience Lab. "
            "Explain the supplied metrics to an operations or engineering decision-maker. "
            "Use exact numbers from the JSON. Separate observation, interpretation, and limitations. "
            "Never claim causality, diagnosis, certification, or guaranteed prediction. "
            "Do not invent variables, events, or benchmarks. Keep the answer under 220 words. "
            f"Write in {language}.\n\n"
            f"User question: {question or 'What should I understand and investigate next?'}\n\n"
            f"Analysis JSON:\n{json.dumps(snapshot, ensure_ascii=False)}"
        )
        response = client.responses.create(model=model, input=prompt)
        text = getattr(response, "output_text", "") or ""
        if not text.strip():
            raise RuntimeError("The model returned an empty response")
        return text.strip(), model
    except Exception as exc:
        fallback = _fallback_narrative(result, lang)
        return f"{fallback}\n\n_AI fallback reason: {type(exc).__name__}._", "deterministic-fallback"


class ResilienceHandler(BaseHTTPRequestHandler):
    server_version = "LambdaSpecLab/1.2"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def _json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _text(self, text: str, content_type: str, status: int = HTTPStatus.OK) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if length <= 0:
            raise ValueError("Request body is required")
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body exceeds the 5 MB limit")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            self._json({"ok": True, "service": "lambda-spec-resilience-lab", "version": "1.2.0"})
            return
        if path == "/api/demos":
            self._json({"demos": [{"id": "degradation", "title": "Network support withdrawal"}, {"id": "telemetry", "title": "Orbital telemetry"}, {"id": "supply-chain", "title": "Supply-chain resilience"}, {"id": "isolated", "title": "Isolated control"}]})
            return
        if path == "/api/demo":
            name = parse_qs(parsed.query).get("name", ["degradation"])[0]
            factory = DEMO_FACTORIES.get(name)
            if not factory:
                self._json({"error": "Unknown demo"}, HTTPStatus.NOT_FOUND)
                return
            self._json(factory())
            return
        if path in {"/", "/index.html"}:
            self._serve_static("index.html")
            return
        if path in {"/styles.css", "/app.js", "/analysis.js"}:
            self._serve_static(path.removeprefix("/"))
            return
        if path.startswith("/assets/"):
            self._serve_static(path.removeprefix("/assets/"))
            return
        self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def _serve_static(self, name: str) -> None:
        safe_name = Path(name).name
        if safe_name != name or safe_name.startswith("."):
            self._json({"error": "Invalid asset path"}, HTTPStatus.BAD_REQUEST)
            return
        file_path = STATIC_DIR / safe_name
        if not file_path.is_file():
            self._json({"error": "Asset not found"}, HTTPStatus.NOT_FOUND)
            return
        content_type, _ = mimetypes.guess_type(file_path.name)
        if file_path.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        elif file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        self._text(file_path.read_text(encoding="utf-8"), content_type or "application/octet-stream")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/analyze":
                self._json({"result": analyze_table(payload)})
                return
            if parsed.path == "/api/explain":
                result = payload.get("result")
                if not isinstance(result, dict):
                    raise ValueError("result must be an analysis object")
                lang = str(payload.get("lang") or "en")
                narrative, engine = _openai_narrative(result, str(payload.get("question") or ""), lang)
                self._json({"narrative": narrative, "engine": engine})
                return
            if parsed.path == "/api/report":
                result = payload.get("result")
                if not isinstance(result, dict):
                    raise ValueError("result must be an analysis object")
                report = markdown_report(result, payload.get("narrative"))
                self._json({"markdown": report})
                return
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self.log_error("Unhandled error: %r", exc)
            self._json({"error": "Internal analysis error"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), ResilienceHandler)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run λ-SPEC Resilience Lab")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args(argv)
    server = create_server(args.host, args.port)
    url_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    url = f"http://{url_host}:{server.server_address[1]}"
    print(f"λ-SPEC Resilience Lab running at {url}")
    print("Press Ctrl+C to stop.")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping λ-SPEC Resilience Lab.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
