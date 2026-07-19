"""Generate an auditable λ-SPEC report without opening the web interface."""
from lambda_spec import analyze_resilience, markdown_report, synthetic

x, env = synthetic.telemetry_subsystems(n=240)
result = analyze_resilience(x, env, system_names=["power", "thermal", "comms"], environment_names=["orbital_cycle", "solar_phase"], window=48, title="Orbital telemetry")
print(markdown_report(result))
