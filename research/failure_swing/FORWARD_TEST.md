# Forward test (registrado el 2026-10-25, antes de que existan los datos)

**Reglas congeladas:** *Support Resistance Breakout Strategy v6.pine* / `strat.breakout` con 4h, periodo 84,
trailing de 4 ATR(14), SMA de 50 días, largos y cortos, reversión ante señal contraria, 0,15% de costes por
lado, 100% del capital por activo.

**Activos:** los 12 pares de Binance de `cross.py`, en cartera equiponderada sin rebalanceo.

**Inicio:** operaciones abiertas desde el 2026-10-25. Los indicadores usan la historia previa como calentamiento.

**Evaluación:** `./prepare_alts.sh && python3 forward.py`, una vez al mes. Decisión a los 6 meses (2027-04-25),
cuando se esperan unas 200-250 operaciones agregadas:

- **Éxito:** media por operación > 0 con t ≥ 2 **y** rentabilidad de la cartera > 0.
- **Fracaso:** t ≤ −1, **o** drawdown de la cartera peor que −35% en cualquier momento (se para antes).
- **En otro caso:** no concluyente. Se amplía a 12 meses con los mismos criterios.

No se cambia ninguna regla durante la prueba. Cualquier variante nueva empieza su propio forward test desde
cero.

## Registro

| Fecha de revisión | Última vela disponible | Operaciones | Media | t | Rentabilidad de la cartera | DD | Estado |
|---|---|---|---|---|---|---|---|
| 2026-10-26 | 2026-10-24 (ninguna posterior al inicio) | 0 | – | – | – | – | En curso, sin datos todavía |

---

# Forward test de la cartera A (registrado el 2026-10-27, antes de que existan los datos)

**Reglas congeladas:** `sharpe/portfolio_a.py`. Aplica la estrategia de ruptura (4h, 84, 4 ATR, SMA de 50 días,
largos y cortos) a los 12 pares de Binance. Cada activo recibe el mismo riesgo: 50% de volatilidad objetivo
dividida entre su volatilidad de 30 días y entre N, con un tope de 2x en bruto. Toda la cartera se escala a un
25% de volatilidad anual (ventana de 30 días, tope de 3x). Todos los tamaños se reajustan una vez al día, con un
coste del 0,15% por lado en cada nocional negociado.

**Inicio:** 2026-10-27. **Evaluación:** `./prepare_alts.sh && python3 sharpe/forward_a.py`, cada mes.

**Criterios**, calibrados con 20.000 trayectorias de 12 meses remuestreadas por bloques del histórico de A
(Sharpe mediano 1,16, p5 −0,35; drawdown p5 −32%, p1 −39%):

- **Parada inmediata:** un drawdown peor que **−39%** en cualquier momento. Por debajo del percentil 1, el
  histórico dejaría de ser una descripción fiable.
- **A los 12 meses (2027-10-27):**
  - Sharpe ≥ 0 y drawdown mejor que −32%: **coherente** con el backtest; se sigue.
  - Sharpe < −0,35 (p5): **fracaso**; se abandona A.
  - Cualquier otro caso: **no concluyente**; se amplía a 24 meses con los mismos criterios.

**Advertencia:** con un año de datos, el error estándar del Sharpe es de ±1. Esta prueba detecta un fallo
grave, pero no puede demostrar por sí sola un Sharpe de 1.

### Registro A

| Fecha de revisión | Días | Rentabilidad | Sharpe | DD | Estado |
|---|---|---|---|---|---|

---

# Forward test de la cartera V6 spot (registrado el 2026-10-27, antes de que existan los datos)

**Reglas congeladas:** `sharpe/portfolio_v6s.py`. Combina dos patas solo de largos en los 12 pares de Binance:
la ruptura (84 / 4 ATR / SMA de 50 días) y el momentum temporal (7/30/90 días). Las dos patas tienen el mismo
riesgo, la cartera se escala a un 25% de volatilidad con un tope de 1x, se reajusta a diario y cada nocional
negociado paga un 0,15% por lado.

**Inicio:** 2026-10-27. **Evaluación:** `python3 sharpe/forward_v6s.py`, cada mes.

**Criterios**, sacados de 10.000 trayectorias de 12 meses del histórico de V6 spot (Sharpe p50 1,27, p5 −0,80;
DD p5 −17%, p1 −20%):

- **Parada inmediata:** un drawdown peor que **−20%**, es decir, por debajo del percentil 1.
- **A los 12 meses (2027-10-27):**
  - Sharpe ≥ 0 y drawdown mejor que −17%: **coherente**.
  - Sharpe < −0,80: **fracaso**.
  - Cualquier otro caso: **no concluyente**; se amplía a 24 meses.

### Registro V6 spot

| Fecha de revisión | Días | Rentabilidad | Sharpe | DD | Estado |
|---|---|---|---|---|---|

---

# Forward test de la estrategia Pine R2a en dos cestas de gráficos (registrado el 2026-10-27, antes de que existan los datos)

**Reglas congeladas:** `single/forward_r2a.py`, que es *Breakout Momentum Vol-Target Strategy v6.pine* con sus
valores por defecto (momentum continuo, umbral de reajuste del 10%, coste del 0,15% por lado). Cada símbolo es un
gráfico con el mismo capital, y la cesta se rebalancea una vez al mes.

**Cestas:**

- **BTC + ETH:** la cesta principal, sin sesgo de selección.
- **Top 5:** BTC, ETH, BNB, SOL y XRP. Elegida con información de hoy, así que esta prueba sirve también para
  medir ese sesgo.

**Inicio:** 2026-10-27. **Evaluación:** `python3 single/forward_r2a.py`, cada mes.

**Criterios**, a partir de 10.000 trayectorias de 12 meses remuestreadas por bloques de 30 días:

| Cesta | Parada inmediata (DD p1) | A los 12 meses: coherente | A los 12 meses: fracaso |
|---|---|---|---|
| BTC + ETH (Sharpe histórico 1,46; Sharpe p50 a 12 meses 1,38) | DD peor que −22% | Sharpe ≥ 0 y DD mejor que −18% | Sharpe < −0,54 |
| Top 5 (Sharpe histórico 1,88; Sharpe p50 a 12 meses 1,77) | DD peor que −17% | Sharpe ≥ 0 y DD mejor que −14% | Sharpe < −0,29 |

En cualquier otro caso, el resultado es no concluyente y la prueba se amplía a 24 meses.

### Registro R2a

| Fecha de revisión | Cesta | Días | Rentabilidad | Sharpe | DD | Estado |
|---|---|---|---|---|---|---|
