"use strict";
const assert = require("node:assert/strict");
const engine = require("../lambda_spec/static/analysis.js");
for (const name of ["degradation", "telemetry", "supply-chain", "isolated"]) {
  const demo = engine.demo(name); const result = engine.analyzeTable(demo);
  assert.ok(result.global.lam >= 0 && result.global.lam <= 1, `${name}: λ bounds`);
  assert.ok(result.global.phi >= 0 && result.global.phi <= 1, `${name}: Φ bounds`);
  assert.ok(result.trajectory.points.length >= 2, `${name}: rolling points`);
  assert.equal(result.withdrawal.length, 11, `${name}: withdrawal length`);
  result.withdrawal.forEach((point, index, curve) => { if (index) assert.ok(point.lambda <= curve[index - 1].lambda + 1e-12, `${name}: monotone envelope`); });
  assert.ok(engine.fallbackNarrative(result, "en").includes("λ="), `${name}: narrative`);
  assert.ok(engine.markdownReport(result).includes("## Limits"), `${name}: report`);
}
const degrading = engine.analyzeTable(engine.demo("degradation"));
assert.equal(degrading.trajectory.trend, "weakening");
console.log("Static analysis engine: all smoke checks passed.");
