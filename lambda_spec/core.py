"""
lambda-spec: fragilidad como limite del acoplamiento.

Phi(x) = lim_{lambda->0} ||H_local(x)|| / ||H(x, E)||

Phi -> 1 : el objeto es todo lo que hay. Fragil.
Phi -> 0 : el objeto es un nodo. Robusto.

La fragilidad no se mide inspeccionando el objeto.
Se mide retirando el entorno.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
from scipy.stats import spearmanr


__all__ = ["CouplingResult", "coupling", "phi", "dlambda_dt", "fragility_report"]


@dataclass
class CouplingResult:
    """Resultado de una medicion de acoplamiento."""

    lam: float          # lambda: fuerza de acoplamiento [0, 1]
    phi: float          # fragilidad [0, 1]
    h_local: float      # norma del sistema aislado
    h_total: float      # norma del sistema acoplado
    n: int              # muestras
    method: str

    @property
    def fragile(self) -> bool:
        """Phi > 0.5: el sistema depende mas de si mismo que de su entorno."""
        return self.phi > 0.5

    def __repr__(self) -> str:
        state = "FRAGIL" if self.fragile else "ROBUSTO"
        return (
            f"CouplingResult(lambda={self.lam:.4f}, phi={self.phi:.4f}, "
            f"n={self.n}, {state})"
        )


def _norm(x: np.ndarray) -> float:
    """Norma L2 normalizada por muestras. Escala-invariante."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    return float(np.sqrt(np.mean(np.sum(x**2, axis=1))))


def coupling(
    x: np.ndarray,
    env: np.ndarray,
    method: str = "spearman",
) -> CouplingResult:
    """
    Mide el acoplamiento entre un sistema x y su entorno env.

    Parameters
    ----------
    x : array (n,) o (n, d)
        Estado del sistema.
    env : array (n,) o (n, m)
        Estado del entorno.
    method : {"spearman", "pearson", "residual"}
        spearman : monotonico, robusto a no-linealidad. Default.
        pearson  : lineal.
        residual : varianza de x explicada por env via minimos cuadrados.

    Returns
    -------
    CouplingResult
    """
    x = np.asarray(x, dtype=float)
    env = np.asarray(env, dtype=float)

    if x.ndim == 1:
        x = x[:, None]
    if env.ndim == 1:
        env = env[:, None]

    if x.shape[0] != env.shape[0]:
        raise ValueError(
            f"x y env deben tener el mismo n: {x.shape[0]} != {env.shape[0]}"
        )

    n = x.shape[0]
    if n < 3:
        raise ValueError(f"n minimo = 3, recibido {n}")

    if method == "residual":
        # lambda = 1 - ||residual|| / ||x||
        env_aug = np.hstack([env, np.ones((n, 1))])
        beta, *_ = np.linalg.lstsq(env_aug, x, rcond=None)
        resid = x - env_aug @ beta
        h_local = _norm(resid)
        h_total = _norm(x)
        lam = 1.0 - (h_local / h_total) if h_total > 0 else 0.0

    else:
        # lambda = |correlacion| media entre cada dim de x y cada dim de env
        corrs = []
        for i in range(x.shape[1]):
            for j in range(env.shape[1]):
                xi, ej = x[:, i], env[:, j]
                if np.std(xi) == 0 or np.std(ej) == 0:
                    corrs.append(0.0)
                    continue
                if method == "spearman":
                    r, _ = spearmanr(xi, ej)
                elif method == "pearson":
                    r = np.corrcoef(xi, ej)[0, 1]
                else:
                    raise ValueError(f"method desconocido: {method}")
                corrs.append(0.0 if np.isnan(r) else abs(float(r)))

        lam = float(np.mean(corrs))
        h_total = _norm(x)
        h_local = h_total * (1.0 - lam)

    lam = float(np.clip(lam, 0.0, 1.0))
    return CouplingResult(
        lam=lam,
        phi=1.0 - lam,
        h_local=h_local,
        h_total=h_total,
        n=n,
        method=method,
    )


def phi(x: np.ndarray, env: np.ndarray, method: str = "spearman") -> float:
    """Atajo: devuelve solo Phi."""
    return coupling(x, env, method=method).phi


def dlambda_dt(
    lam_series: np.ndarray,
    t: Optional[np.ndarray] = None,
) -> float:
    """
    Condicion de existencia: dlambda/dt > 0.

    Si lambda deja de crecer, Phi -> 1 y el sistema colapsa
    a su propio H_local.

    Returns
    -------
    float : pendiente. Negativa = colapso en curso.
    """
    lam_series = np.asarray(lam_series, dtype=float)
    if len(lam_series) < 2:
        raise ValueError("se requieren >= 2 puntos")
    if t is None:
        t = np.arange(len(lam_series), dtype=float)
    slope, _ = np.polyfit(t, lam_series, 1)
    return float(slope)


def fragility_report(
    x: np.ndarray,
    env: np.ndarray,
    name: str = "sistema",
    method: str = "spearman",
) -> str:
    """Reporte legible de una sola medicion."""
    r = coupling(x, env, method=method)
    state = "FRAGIL" if r.fragile else "ROBUSTO"
    bar_len = int(r.lam * 40)
    bar = "#" * bar_len + "-" * (40 - bar_len)

    return (
        f"\n  {name}\n"
        f"  {'-' * 52}\n"
        f"  lambda  {r.lam:.4f}  [{bar}]\n"
        f"  Phi     {r.phi:.4f}\n"
        f"  n       {r.n}\n"
        f"  metodo  {r.method}\n"
        f"  estado  {state}\n"
    )
