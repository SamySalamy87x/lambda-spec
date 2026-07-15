"""
lambda-spec en 5 minutos.

    python examples/quickstart.py
"""

import numpy as np
from lambda_spec import dlambda_dt, fragility_report, synthetic

print("=" * 54)
print("  lambda-SPEC v1.1  --  Phi = lim ||H_local|| / ||H||")
print("=" * 54)

# 1. Switch bistable (OXPHOS hepatico)
x, env = synthetic.bistable_switch()
print(fragility_report(x, env, "OXPHOS hepatico (bistable)"))

# 2. Acoplamiento neural (Samy-Link BCI)
x, env = synthetic.neural_coupling()
print(fragility_report(x, env, "BCI neural (N=24)"))

# 3. Telemetria (ORION OPS)
x, env = synthetic.telemetry_subsystems()
print(fragility_report(x, env, "Telemetria: subsistemas"))

# 4. Control negativo: sistema aislado
x, env = synthetic.isolated_system()
print(fragility_report(x, env, "Sistema aislado (control)"))

# 5. Condicion de existencia
print("  Condicion de existencia: dlambda/dt > 0")
print("  " + "-" * 52)

creciendo = np.array([0.20, 0.31, 0.44, 0.55, 0.68])
colapsando = np.array([0.68, 0.55, 0.44, 0.31, 0.20])

for label, serie in [("acoplando", creciendo), ("colapsando", colapsando)]:
    d = dlambda_dt(serie)
    veredicto = "estable" if d > 0 else "COLAPSO EN CURSO"
    print(f"  {label:12s}  dlambda/dt = {d:+.4f}   {veredicto}")

print()
print("=" * 54)
print("  El objeto no dice si es fragil.")
print("  Solo lo dice retirar el entorno.")
print("=" * 54)
