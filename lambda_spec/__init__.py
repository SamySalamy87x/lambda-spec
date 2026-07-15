"""lambda-spec: fragilidad como limite del acoplamiento."""

from lambda_spec.core import (
    CouplingResult,
    coupling,
    phi,
    dlambda_dt,
    fragility_report,
)
from lambda_spec import synthetic

__version__ = "1.1.0"
__all__ = [
    "CouplingResult",
    "coupling",
    "phi",
    "dlambda_dt",
    "fragility_report",
    "synthetic",
]
