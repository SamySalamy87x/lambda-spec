# OpenAI Build Week submission package

## Project title

**λ-SPEC Resilience Lab — Measure decoupling before failure becomes obvious**

## Category

**Work and productivity**

## One-line description

An auditable resilience-analysis product that measures how strongly a system depends on its environment, tracks early decoupling through `dλ/dt`, stress-tests environmental withdrawal, and explains only what the evidence supports.

## Public description

Most risk tools inspect the object: its internal quality, failure count, or current condition. λ-SPEC asks a different operational question: **what remains when the environment that sustains the system is progressively withdrawn?**

A user loads a CSV, labels system and environment variables, and receives:

- global coupling `λ` and fragility `Φ`;
- rolling coupling and `dλ/dt` trajectory;
- a controlled environmental-withdrawal stress envelope;
- ranked environmental drivers;
- explicit confidence, data-quality, evidence, and limitation sections;
- JSON, Markdown, and print/PDF outputs;
- an optional GPT interpretation constrained to the measured metrics.

The product runs in two modes. A static browser engine performs the complete analysis locally, so uploaded data never needs to leave the browser. The Python reference server exposes the same workflow and can call the OpenAI Responses API. If the API is absent or fails, the system returns a deterministic evidence summary rather than breaking.

## Problem

Organizations often evaluate resilience by inspecting internal performance. That can miss a system that looks healthy only because external support is compensating for hidden fragility. Analysts then spend hours manually testing dependencies, comparing windows, and preparing reports, while ordinary dashboards show symptoms after coupling has already deteriorated.

## Solution

λ-SPEC treats fragility as a property of coupling rather than an isolated object score. It converts ordinary tabular data into an inspectable chain:

```text
measure λ → track rolling λ → calculate dλ/dt → withdraw signal → rank drivers → explain limits
```

Every displayed conclusion is tied to exportable metrics. The AI layer cannot invent drivers or claim causality because it receives a compact result snapshot and explicit evidence boundaries.

## What was built during Build Week

The pre-event artifact was a minimal Python reference library with four primitive functions and synthetic controls. The Build Week product layer adds:

1. complete Resilience Lab interface;
2. CSV upload and column-role mapping;
3. browser-local analysis engine with no server dependency;
4. rolling coupling and `dλ/dt` analysis;
5. environmental-withdrawal stress envelope;
6. drop-one environmental-driver ranking;
7. data-quality and confidence reporting;
8. optional OpenAI Responses API interpretation with deterministic fallback;
9. JSON, Markdown, and print/PDF exports;
10. bilingual English/Spanish interface;
11. Python HTTP product server;
12. Docker packaging and health check;
13. automated Python and JavaScript test suites;
14. GitHub Pages static deployment workflow;
15. submission copy and a sub-three-minute demonstration script.

This separation makes the Build Week delta visible in the commit history and keeps the earlier mathematical core independently inspectable.

## Technical implementation

### Core

- Python 3.9+
- NumPy and SciPy
- Spearman, Pearson, and residual-reconstruction coupling methods
- JSON-serializable analysis contract

### Product server

- Python standard-library `ThreadingHTTPServer`
- no web-framework runtime dependency
- 5 MB request limit
- input validation, safe static-file routing, and security headers
- `/api/health`, `/api/demo`, `/api/analyze`, `/api/explain`, `/api/report`

### Static application

- accessible HTML/CSS/JavaScript
- browser-local numerical engine
- Canvas charts without external charting libraries
- responsive layout and print stylesheet
- four deterministic demonstrations

### OpenAI integration

- Responses API through the official Python SDK when `OPENAI_API_KEY` is configured
- configurable `OPENAI_MODEL`
- evidence-only prompt with numerical snapshot
- explicit prohibition on causal, diagnostic, certification, and guaranteed-prediction claims
- deterministic fallback when no key is available

## Use of Codex and GPT-5.6

Use the final Codex session to inspect and verify the repository rather than merely asking for boilerplate. The intended evidence trail is:

1. ask Codex to review the repository architecture and Build Week delta;
2. ask it to run the Python and JavaScript test suites;
3. ask it to start the server and smoke-test the four user flows;
4. ask it to inspect data validation, static fallback, and OpenAI failure handling;
5. ask it to make only necessary fixes and summarize each decision;
6. run `/feedback` in that same session and copy the generated session ID into Devpost.

Exact final-pass prompt: [`CODEX_FINAL_PASS.md`](CODEX_FINAL_PASS.md).

Do not claim a Codex session ID until `/feedback` has actually produced one.

## Why the idea is differentiated

- It measures coupling loss rather than another internal risk score.
- It turns a compact mathematical thesis into a complete product workflow.
- It works without sending data to a hosted service.
- It pairs AI interpretation with a deterministic numerical and reporting substrate.
- It exposes uncertainty and limitations as first-class output instead of fine print.
- The negative control demonstrates that a coherent isolated system can still be fragile under the λ-SPEC definition.

## Evaluation-criteria alignment

### Technological implementation

- dual Python/browser implementations;
- rolling and perturbation analysis;
- optional model integration with graceful degradation;
- automated tests and deployable packaging;
- auditable JSON contract and reproducible demonstrations.

### Design

- complete onboarding from data to export;
- bilingual, responsive interface;
- visible loading, success, error, data-quality, and confidence states;
- no external UI or chart dependency;
- static mode remains fully functional.

### Potential impact

The same workflow can support operational telemetry, supply chains, service systems, AI-agent evaluation, portfolios of dependencies, and research data. It reduces manual dependency exploration and produces a reviewable decision artifact in minutes.

### Idea quality

The central thesis is not “use AI to analyze a CSV.” It is a specific measurement model: fragility emerges when environmental coupling is withdrawn. The AI is subordinate to the measurable method.

## Demonstration flow

Use the script in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). The strongest default demonstration is **Network support withdrawal** because the rolling chart visibly weakens while the global metric alone remains less obvious.

## Repository and run commands

```bash
python -m pip install -e ".[test]"
pytest -q
node tests/js_smoke.js
lambda-spec-lab --open-browser
```

Docker:

```bash
docker build -t lambda-spec .
docker run --rm -p 8000:8000 lambda-spec
```

## Required Devpost assets

- Public repository URL: `https://github.com/SamySalamy87x/lambda-spec`
- Public application URL: use the GitHub Pages deployment produced by the Pages workflow, or deploy the Docker image to any public container host.
- Public YouTube video under three minutes.
- Project description based on this document.
- `/feedback` ID from the final Codex session.
- Category: Work and productivity.

## Claims and limitations

λ-SPEC measures observed association and withdrawal sensitivity. It does not establish causality, clinical diagnosis, financial suitability, safety certification, or guaranteed future failure. Unmeasured variables, sampling choices, temporal aggregation, and nonstationarity can alter the result.
