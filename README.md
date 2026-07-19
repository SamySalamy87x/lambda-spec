<p align="center">
  <strong style="font-size: 2rem">λ-SPEC Resilience Lab</strong><br>
  <em>See what remains when the environment is withdrawn.</em>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#what-the-product-does">Product</a> ·
  <a href="#scientific-core">Scientific core</a> ·
  <a href="HACKATHON_SUBMISSION.md">Build Week submission</a>
</p>

# λ-SPEC v1.2

λ-SPEC is an executable method and product for measuring **system–environment coupling**. It estimates whether a system remains robust because it is well coupled to its environment, or becomes fragile when that support is withdrawn.

The Resilience Lab converts a CSV into an auditable decision package:

- global coupling `λ` and complementary fragility `Φ = 1 − λ`;
- rolling coupling and `dλ/dt` as an early decoupling signal;
- an environmental-withdrawal stress envelope;
- drop-one ranking of measured environmental drivers;
- explicit data-quality, confidence, evidence, and limitation sections;
- JSON, Markdown, and print/PDF exports;
- an optional OpenAI Responses API interpretation constrained to the measured evidence.

The application is **static-first**: every core analysis can run locally in the browser, including CSV upload. The Python server provides the reference implementation and can add the optional OpenAI interpretation. No third-party frontend framework or charting dependency is required.

## Quick start

### Browser-only mode

Open `lambda_spec/static/index.html`, or publish that directory as a static site. The browser computes the analysis locally and includes four demonstrations.

### Python product mode

```bash
python -m pip install -e .
lambda-spec-lab --open-browser
```

Then open `http://127.0.0.1:8000`.

Alternative:

```bash
python -m lambda_spec.webapp --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t lambda-spec .
docker run --rm -p 8000:8000 lambda-spec
```

### Optional evidence interpreter

The product remains fully functional without an API key. To enable the OpenAI-backed interpretation, provide the key to the server environment and optionally choose the model:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5.6"
lambda-spec-lab
```

The model receives a compact metric snapshot, not the entire raw dataset. Its instruction prohibits causal, clinical, certification, or guaranteed-prediction claims. If the request fails, the app returns a deterministic local interpretation.

## What the product does

1. **Choose evidence** — load a built-in scenario or upload a CSV.
2. **Map the system** — mark columns as system, environment, or ignored.
3. **Measure** — calculate global `λ`, `Φ`, and state.
4. **Track** — calculate rolling `λ` and `dλ/dt`.
5. **Stress** — progressively replace environmental signal with independently permuted observations and measure the monotone resilience envelope.
6. **Rank** — remove one environmental variable at a time and measure the loss of `λ`.
7. **Explain and export** — create an evidence-bounded interpretation and download the auditable metrics.

Built-in demonstrations:

| Demo | Purpose |
|---|---|
| Network support withdrawal | Shows progressive decoupling and a weakening `dλ/dt` |
| Orbital telemetry | Multi-subsystem operational coupling |
| Supply-chain resilience | Demand, supplier, and transport dependence |
| Isolated-system control | Negative control expected to produce high `Φ` |

## Scientific core

```text
Φ(x) = lim        ‖H_local(x)‖
       λ → 0      ─────────────
                  ‖H(x, E)‖
```

- `Φ → 1`: the object is mostly its isolated dynamics — fragile under withdrawal.
- `Φ → 0`: the object behaves as a coupled node — robust under the measured environment.
- Existence condition: `dλ/dt > 0`; a persistently negative trajectory is treated as a decoupling warning, not proof of inevitable collapse.

### Python API

```python
from lambda_spec import analyze_resilience, markdown_report, synthetic

x, env = synthetic.telemetry_subsystems(n=240)
result = analyze_resilience(
    x,
    env,
    system_names=["power", "thermal", "comms"],
    environment_names=["orbital_cycle", "solar_phase"],
    window=48,
    title="Orbital telemetry",
)

print(result["global"])
print(markdown_report(result))
```

Low-level API:

| Function | Output |
|---|---|
| `coupling(x, env, method=)` | `CouplingResult`: λ, Φ, norms, sample count |
| `phi(x, env)` | Φ only |
| `dlambda_dt(series, t=None)` | λ slope |
| `analyze_resilience(...)` | Complete JSON-serializable product analysis |
| `markdown_report(result)` | Auditable Markdown report |

Methods:

- `spearman` — monotonic association; default.
- `pearson` — linear association.
- `residual` — normalized residual energy after least-squares environmental reconstruction.

## Architecture

```text
CSV / demo
    │
    ├── browser-local engine (analysis.js)
    │      └── static deployment, no server required
    │
    └── Python reference server (webapp.py)
           ├── analysis.py → rolling, withdrawal, ranking, reports
           ├── core.py → λ / Φ primitives
           └── optional OpenAI Responses API interpretation
```

The browser and Python implementations use the same narrow analysis chain. The Python path is the canonical reference; the browser path preserves a zero-dependency public demo and keeps uploaded data local.

## Validation

```bash
python -m pip install -e ".[test]"
pytest -q
node tests/js_smoke.js
```

Current test surface:

- original λ/Φ mathematical invariants and controls;
- method directionality;
- rolling and withdrawal behavior;
- data-quality and overlap validation;
- Markdown audit sections;
- live HTTP health, demo, analysis, and interpretation fallback;
- static-browser engine smoke test.

## Scope and limitations

λ-SPEC measures observed coupling. It does **not** by itself establish causality, clinical diagnosis, financial suitability, engineering certification, or a guaranteed forecast. Results depend on the variables and time range supplied. The withdrawal curve is a controlled stress-test envelope, not a literal simulation of every real intervention.

The implementation is intentionally transparent and compact so a reviewer can inspect the computation without a proprietary service.

## Original reference implementation

Earlier λ-SPEC v1.1 validated the minimal formalism with synthetic controls and exposed `coupling`, `phi`, `dlambda_dt`, and `fragility_report`. Version 1.2 preserves that API and adds the complete Resilience Lab product layer.

Previous name: FI-SPEC v1.0, renamed to avoid collision with established clinical and state fragility indices.

## License and author

MIT License.

Omar Rafael Pérez Gallardo — OMROS LAB, Querétaro, Mexico  
ORCID: `0009-0008-8328-6978`
