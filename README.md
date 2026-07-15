# λ-SPEC v1.1

**Fragilidad como límite del acoplamiento.**

```
Φ(x) = lim   ‖H_local(x)‖ / ‖H(x, E)‖
      λ→0
```

- `Φ → 1` — el objeto es todo lo que hay. **Frágil**, aunque sea excelente.
- `Φ → 0` — el objeto es un nodo. **Robusto**, aunque sea mediocre.

---

## La tesis

La fragilidad no es propiedad del objeto. Es propiedad del acoplamiento.

Los índices de fragilidad existentes miden el objeto: cuántos eventos tumban un RCT, qué tan quebrado está un Estado. Un número, una foto. λ-SPEC mide otra cosa — qué queda cuando el entorno se retira.

**Corolario.** El sustrato causal no aporta información: es obvio y es causa de sí mismo. Por lo tanto Φ es medible *solo* removiendo el acoplamiento, nunca inspeccionando el objeto.

**Condición de existencia.** `dλ/dt > 0`. Si λ deja de crecer, Φ→1 y el sistema colapsa a su propio H_local. Aplica al hígado, a la telemetría, al portafolio — y a λ-SPEC mismo. Autorreferencial por construcción: no es defecto, es la prueba.

---

## Instalación

```bash
pip install -e .
python examples/quickstart.py
```

Cinco minutos. Datos sintéticos incluidos. Cero dependencias externas más allá de numpy y scipy.

---

## Uso

```python
from lambda_spec import coupling, synthetic

x, env = synthetic.bistable_switch()
r = coupling(x, env)

print(r)          # CouplingResult(lambda=0.9462, phi=0.0538, n=200, ROBUSTO)
print(r.fragile)  # False
```

Condición de existencia sobre una serie temporal:

```python
from lambda_spec import dlambda_dt

dlambda_dt([0.20, 0.31, 0.44, 0.55, 0.68])   # +0.1200  estable
dlambda_dt([0.68, 0.55, 0.44, 0.31, 0.20])   # -0.1200  COLAPSO EN CURSO
```

---

## API

| Función | Devuelve |
|---|---|
| `coupling(x, env, method=)` | `CouplingResult` — λ, Φ, H_local, H_total |
| `phi(x, env)` | `float` — solo Φ |
| `dlambda_dt(serie, t=None)` | `float` — pendiente. Negativa = colapso |
| `fragility_report(x, env, name)` | `str` — reporte legible |

**Métodos:** `spearman` (default, monotónico, robusto a no-linealidad) · `pearson` (lineal) · `residual` (varianza explicada vía mínimos cuadrados)

---

## Validación

Salida real de `quickstart.py`:

| Dominio | λ | Φ | Estado |
|---|---|---|---|
| OXPHOS hepático (bistable) | 0.946 | 0.054 | ROBUSTO |
| BCI neural (N=24) | 0.587 | 0.413 | ROBUSTO |
| Telemetría: subsistemas | 0.472 | 0.528 | FRÁGIL |
| Sistema aislado (control) | 0.082 | **0.918** | FRÁGIL |

El control negativo separa limpiamente: un sistema sin acoplamiento da Φ=0.918 aunque su estructura interna sea perfectamente coherente. Eso es la tesis, medida.

```bash
python -m pytest tests/ -q
# 8 passed
```

---

## Alcance

Esta es la implementación de referencia — mínima, ejecutable, verificable por un desconocido sin abrir un issue. No es el pipeline completo.

Las validaciones empíricas (OXPHOS r=0.983 en 4/5 datasets NASA OSDR · Samy-Link N=24 LOSO · ORION-HEALTH ρ=0.94 · ORION OPS 2.59M muestras) viven en sus repos respectivos. Aquí sólo está el formalismo y su prueba sintética.

---

## Nomenclatura

Antes: FI-SPEC v1.0 (DOI 10.5281/zenodo.20724294).

Renombrado a λ-SPEC para eliminar la colisión con el *Fragility Index* clínico (Walsh et al., 2014) y el *Fragile States Index*. Ambos miden el objeto; λ-SPEC mide el acoplamiento. El nombre anterior enterraba la distinción en cada búsqueda.

---

## Licencia

MIT.

Omar Rafael Pérez Gallardo — OMROS LAB, Querétaro
ORCID [0009-0008-8328-6978](https://orcid.org/0009-0008-8328-6978)
