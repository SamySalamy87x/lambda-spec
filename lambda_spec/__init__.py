"""lambda-spec: fragilidad como limite del acoplamiento."""
from lambda_spec.core import CouplingResult, coupling, phi, dlambda_dt, fragility_report
from lambda_spec.analysis import analyze_resilience, markdown_report
from lambda_spec import synthetic

__version__ = "1.2.0"
__all__ = ["CouplingResult", "coupling", "phi", "dlambda_dt", "fragility_report", "analyze_resilience", "markdown_report", "synthetic"]
