# Final Codex verification prompt

Open this repository at the current Build Week branch and perform a release-blocking verification of λ-SPEC Resilience Lab.

Do not redesign the product or add speculative features. Work through the following sequence and continue until every feasible check is green:

1. Read `README.md`, `HACKATHON_SUBMISSION.md`, `lambda_spec/core.py`, `lambda_spec/analysis.py`, `lambda_spec/webapp.py`, and the three static files.
2. Inspect the git history and distinguish the pre-existing v1.1 mathematical core from the v1.2 Build Week product layer.
3. Install the project with test dependencies.
4. Run `pytest -q`.
5. Run `node tests/js_smoke.js`.
6. Start `lambda-spec-lab` on an available local port and verify:
   - `/api/health`;
   - all four demos;
   - CSV analysis;
   - system/environment role validation;
   - rolling trajectory;
   - withdrawal envelope;
   - driver ranking;
   - deterministic interpretation without an API key;
   - JSON and Markdown report generation;
   - static browser-only mode.
7. Review security and robustness: request-size limit, path traversal resistance, invalid JSON, missing columns, nonnumeric rows, overlapping roles, no secret exposure, and OpenAI failure fallback.
8. Inspect responsive and accessible behavior at desktop, tablet, and mobile sizes.
9. Make only fixes required for correctness, reliability, accessibility, or submission readiness. Add tests for any bug fixed.
10. Re-run all checks and provide a concise release report containing exact commands and results.
11. Confirm that no statement in the README or submission package claims a capability that was not verified.
12. At the end of this same Codex session, run `/feedback` and provide the session ID for the Devpost form.

Constraints:

- Preserve the public low-level API.
- Preserve static-first functionality.
- Do not introduce a frontend framework or external charting library.
- Do not require an OpenAI key for the core product.
- Do not state that coupling proves causation or guarantees failure.
