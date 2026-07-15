"""
Datos sinteticos para validar lambda-spec sin dependencias externas.

Cuatro generadores que replican la estructura de los dominios
donde el formalismo ya fue validado empiricamente.
"""

import numpy as np

__all__ = [
    "bistable_switch",
    "neural_coupling",
    "telemetry_subsystems",
    "isolated_system",
]


def bistable_switch(n: int = 200, coupling: float = 0.95, seed: int = 0):
    """
    Switch bistable tipo OXPHOS hepatico.

    El sistema salta entre dos estados. El entorno predice el salto.
    Acoplamiento alto -> Phi bajo -> robusto.

    Returns
    -------
    x   : (n,) estado del sistema
    env : (n, 2) entorno
    """
    rng = np.random.default_rng(seed)
    driver = np.cumsum(rng.normal(0, 1, n))
    driver = (driver - driver.mean()) / driver.std()

    state = np.tanh(3.0 * driver)
    noise = rng.normal(0, 1 - coupling + 1e-6, n)
    x = state + noise

    env = np.column_stack([driver, np.roll(driver, 1)])
    return x, env


def neural_coupling(n: int = 24, n_channels: int = 4, seed: int = 1):
    """
    Acoplamiento neural tipo Samy-Link BCI (N=24, LOSO).

    Canales corticales acoplados a una fase comun.
    """
    rng = np.random.default_rng(seed)
    phase = rng.uniform(0, 2 * np.pi, n)
    x = np.column_stack([
        np.sin(phase + k * 0.3) + rng.normal(0, 0.15, n)
        for k in range(n_channels)
    ])
    env = np.column_stack([np.sin(phase), np.cos(phase)])
    return x, env


def telemetry_subsystems(n: int = 500, seed: int = 2):
    """
    Subsistemas de telemetria tipo ORION OPS.

    Potencia, termica y comunicaciones acopladas a un ciclo orbital.
    """
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 8 * np.pi, n)
    orbital = np.sin(t)

    power = 0.8 * orbital + rng.normal(0, 0.2, n)
    thermal = 0.6 * np.roll(orbital, 5) + rng.normal(0, 0.25, n)
    comms = 0.7 * orbital + rng.normal(0, 0.3, n)

    x = np.column_stack([power, thermal, comms])
    env = np.column_stack([orbital, np.cos(t)])
    return x, env


def isolated_system(n: int = 200, seed: int = 3):
    """
    Sistema aislado: lambda -> 0, Phi -> 1.

    Control negativo. Excelente internamente, sin acoplamiento.
    Fragil por definicion.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    env = rng.normal(0, 1, (n, 2))
    return x, env
