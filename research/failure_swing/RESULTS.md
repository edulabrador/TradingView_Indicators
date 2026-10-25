# Failure Swing Strategy: análisis de rentabilidad

**Conclusión: la estrategia no es rentable.** Con sus parámetros por defecto pierde dinero en BTC/USD en todas
las temporalidades probadas (15m a 1D) entre agosto de 2018 y octubre de 2026, tanto en la versión v3 original
como en la v6. Sigue perdiendo con comisión cero en casi todas, y ninguna combinación de parámetros de una
rejilla de 192 mantiene beneficios fuera de muestra con un número de operaciones mínimamente significativo.
En el mismo periodo, comprar y mantener BTC dio aproximadamente +970%.

## Metodología

- **Datos:** BTC/USD de Bitstamp, velas de 1 minuto ([ff137/bitstamp-btcusd-minute-data](https://github.com/ff137/bitstamp-btcusd-minute-data)),
  del 01/01/2017 al 25/10/2026, sin huecos. Las velas de cada temporalidad se agregan a partir de los minutos.
  2017 y julio de 2018 solo sirven de calentamiento; se opera desde el 01/08/2018, la fecha por defecto del script.
- **Motor (`bt.py`):** replica el emulador de TradingView. Las señales se calculan al cierre de la vela y la
  orden se ejecuta en la apertura de la siguiente. Se invierte el 100% del capital, con comisión del 0,2% por
  lado y `pyramiding=0` (una señal contraria invierte la posición).
  - `v3`: salidas con `strategy.close()` evaluadas al cierre, ejecutadas en la apertura siguiente.
  - `v6`: stop y TP como órdenes stop/limit. Qué se toca antes dentro de la vela se resuelve con los datos de
    1 minuto; si stop y TP caen en el mismo minuto, se asume el stop (criterio conservador). También existe el
    modo `ohlc`, que usa la heurística por defecto de TradingView; los resultados coinciden con los de 1 minuto.
- **Sin modelar:** deslizamiento, spread y la financiación de los cortos (en spot no se puede ir corto; en
  futuros hay funding). Todo ello empeoraría los resultados.

## 1. Parámetros por defecto (84 / EMA 120 / filtro 5% / SL 2%)

| TF | Versión | Operaciones | % aciertos | Profit factor | CAGR | Máx. DD |
|---|---|---|---|---|---|---|
| 15m | v6 | 213 | 34% | 0,71 | −15% | −78% |
| 30m | v6 | 288 | 35% | 0,93 | −10% | −66% |
| 1h | v6 | 339 | 30% | 0,72 | −23% | −89% |
| 2h | v6 | 317 | 26% | 0,72 | −21% | −87% |
| 4h | v6 | 265 | 24% | 0,85 | −16% | −78% |
| 6h | v6 | 196 | 20% | 0,85 | −14% | −79% |
| 12h | v6 | 117 | 16% | 0,55 | −14% | −73% |
| 1D | v6 | 79 | 11% | 0,45 | −12% | −67% |

La versión v3 da resultados del mismo orden: CAGR entre −12% y −22% (tabla completa en `baseline.py`).
El filtro "Only trade towards the EMA" solo cambia una operación de cada temporalidad. El filtro de
volatilidad ya impide casi siempre que se entre con el TP por detrás del precio.

## 2. Por qué pierde (4h)

- Las salidas solo pueden ser dos: stop (76% de las operaciones, −2,2% bruto de media) o TP (24%, +6,7% bruto).
- Con un 0,4% de comisión por operación completa, la pérdida neta es de −2,6% y la ganancia de +6,3%. Para no
  perder hace falta acertar `2,6 / (6,3 + 2,6) = 29%` de las veces. La estrategia acierta el 24%.
- Los **cortos son el problema principal**: −0,74% neto por operación (t = −2,4) frente a ~0% de los largos.
  Vender en contra de cada "falsa ruptura" de máximos durante un mercado alcista de 8 años sale muy caro.
  Solo largos, en 4h: PF 1,07, pero −10% de rendimiento total y −48% de drawdown. Sigue sin ser invertible.
- Ningún año completo cierra en positivo en 4h (2019–2025: entre −5% y −25% cada año).

## 3. Comisiones

Profit factor según la comisión por lado:

| TF | 0% | 0,05% | 0,1% | 0,2% |
|---|---|---|---|---|
| 30m | 1,06 | 1,03 | 0,99 | 0,93 |
| 1h | 0,84 | 0,80 | 0,78 | 0,72 |
| 4h | 0,93 | 0,91 | 0,89 | 0,85 |
| 1D | 0,52 | 0,50 | 0,48 | 0,45 |

El problema no son las comisiones: sin ellas tampoco hay ventaja. El único caso por encima de 1 (30m sin
comisión) no resiste ninguna comisión realista.

## 4. Entradas aleatorias con las mismas salidas

Se generaron 100 simulaciones por temporalidad con el mismo número de señales largas y cortas, colocadas en
velas al azar que cumplen el filtro de volatilidad, y con las mismas reglas de stop y TP:

| TF | PF real | PF aleatorio (mediana) | Percentil 95 aleatorio |
|---|---|---|---|
| 1h | 0,72 | 0,48 | 0,66 |
| 4h | 0,85 | 0,59 | 0,94 |
| 1D | 0,45 | 0,53 | 1,17 |

En 1h y 4h la señal de falsa ruptura **sí tiene algo de información**: en 1h supera las 100 simulaciones
aleatorias. Pero la estructura de salidas (stop ajustado y TP lejano en la EMA) pierde tanto que esa ventaja no
basta. En 1D la señal no se distingue del azar.

## 5. Robustez de parámetros (validación fuera de muestra)

Rejilla de 192 combinaciones: periodo S/R {24, 42, 84, 168} × EMA {50, 120, 200} × filtro {0, 2, 5, 8}% ×
SL {1, 2, 3, 5}%. Muestra de entrenamiento (IS) 2018-08 → 2022, fuera de muestra (OOS) 2023 → 2026-10.

| TF | % combinaciones PF>1 en IS | % PF>1 en OOS | % con CAGR>0 en todo el periodo |
|---|---|---|---|
| 1h | 8% | 21% | 8% |
| 4h | 7% | 0% | 0% |
| 1D | 0% | 5% | 0% |

- En 4h, las 5 mejores combinaciones de IS (PF 1,0–1,14) dan PF 0,40–0,48 en OOS.
- En 1h, las mejores de IS (PF 1,27–1,44) solo hacen **3 operaciones** en OOS. Su PF de 6 a 49 es ruido.
- Ningún parámetro tiene un efecto sistemático que convierta la estrategia en ganadora. Un filtro de
  volatilidad más alto y un periodo largo "pierden menos" porque operan menos.

## Limitaciones

- Solo BTC/USD (Bitstamp). Otros activos o exchanges pueden dar cifras distintas, aunque nada en estos
  resultados indica que la lógica funcione en otro sitio.
- El motor replica las reglas de TradingView, pero no es TradingView. El Strategy Tester puede diferir en
  detalles como el redondeo de cantidades o el margen.

## Cómo reproducirlo

```bash
cd research/failure_swing
python3 prepare_data.py   # descarga ~150 MB y genera data/min.npz
python3 baseline.py       # tabla 1 (y genera data/bars.pkl)
python3 by_year.py        # sección 2
python3 robustness.py     # secciones 3, 4 y 5 (~10 min con 4 núcleos)
```

---

# Iteraciones para hacerla rentable

## Protocolo

- **Costes:** 0,15% por lado (0,1% de comisión y 0,05% de deslizamiento), con prueba de estrés al 0,25%.
- **Datos:** BTC/USD de Bitstamp desde 2013-06 (`min_full.npz`).
  - Desarrollo: 2018-08 → 2022.
  - Validación: 2023-2024.
  - Dos reservas que no se tocaron hasta la decisión final: 2014-2017 (otro régimen de mercado) y 2025-01 → 2026-10.
  - No hubo acceso a datos de otros activos: los hosts de exchanges están bloqueados en el entorno.
- **Criterios de éxito, fijados antes de abrir las reservas:**
  1. CAGR > 0 y PF > 1 en validación y en ambas reservas.
  2. Entradas aleatorias superadas con p < 0,05.
  3. Resultado positivo con costes del 0,25%.
  4. Al menos el 80% de las configuraciones vecinas positivas.

## Iteración 1: filtros sobre la falsa ruptura (`dev_grid.py`, 1.728 variantes)

Se probaron filtro de tendencia (SMA de 50 o 200 días), dirección (solo largos, solo cortos o ambos), stop bajo
la mecha ± ATR, objetivos de 1R/2R/3R o la EMA, y salida por tiempo, en 1h, 4h y 1D. **El mejor estadístico t
fue 1,58.** Con 1.728 variantes, el máximo esperable por azar ronda 3,3, así que no hay ventaja demostrable.

## Iteración 2: confirmar el barrido de stops (`dev_grid2.py`, 384 variantes)

Se añadieron un rechazo fuerte (cierre en el 40% de la vela más alejado de la mecha), volumen anómalo
(z ≥ 1,5), un objetivo de 5R y trailing stops. Las medianas de toda la familia pasaron a ser positivas en
desarrollo (t ≈ 0,7, PF ≈ 1,25). Una configuración elegida por medianas, no por máximo (`cand.py`), batía a
las entradas aleatorias en desarrollo, pero **falló en la validación 2023-24**: PF de 0,36 a 1,01 según la
temporalidad. Descartada.

## Estudio de eventos (`event.py`, 2018-08 → 2024)

Mide, sin reglas de salida, el retorno posterior a cada evento en unidades de ATR, comparado con todas las velas
del mismo régimen. Se hizo para 5 temporalidades, 3 periodos y 3 regímenes.

- **Falsa ruptura** (la premisa de la estrategia): estadístico t negativo en casi todas las celdas, entre −1 y −4.
  Tras barrer un mínimo y cerrar dentro, el precio sigue cayendo. Tras barrer un máximo, sigue subiendo.
  **La premisa es falsa en BTC.**
- **Ruptura real** (cierre más allá del nivel): continuación con t entre +3 y +6 en todas las temporalidades y
  periodos, también dentro del mismo régimen de tendencia. Es el conocido efecto de momentum en series
  temporales.

## Iteración 3: operar la ruptura de los mismos niveles (`bo_grid.py`, 320 variantes)

Mismos niveles de 84 velas que la estrategia original, pero con entrada al cerrar más allá del nivel y salida
por trailing de k·ATR. En desarrollo, el 78% de las variantes es rentable, y en 4h hay una meseta estable
(Sharpe de 0,6 a 1,2 para periodos de 42-168 y k de 3-5). Se eligió el centro de esa meseta, no el máximo:
**4h, periodo 84, trailing de 4 ATR, filtro SMA de 50 días, largos y cortos**. Esta es la estrategia
*Support Resistance Breakout Strategy v6.pine*.

### Resultados fuera de muestra (`final.py`, `final_tests.py`)

| Periodo | Operaciones | PF | CAGR | Máx. DD | Sharpe | Comprar y mantener (CAGR / DD / Sharpe) |
|---|---|---|---|---|---|---|
| Desarrollo 2018-08 → 2022 | 79 | 2,46 | +64% | −41% | 1,27 | +20% / −77% / 0,61 |
| Validación 2023-24 | 44 | 1,71 | +32% | −31% | 1,00 | +138% / −30% / 2,01 |
| Reserva 2014-2017 | 68 | 3,48 | +116% | −35% | 1,76 | +108% / −82% / 1,35 |
| **Reserva 2025 → 2026-10** | 42 | **0,86** | **−10%** | −28% | −0,24 | −8% / −54% / 0,02 |

Con costes del 0,25% por lado, el CAGR baja a +26% en validación, a +108% en 2014-17 y a −14% en 2025-26.
Configuraciones vecinas (periodo {42, 84, 168} × k {3, 4, 5} × dirección): positivas el 94% en validación, el
100% en 2014-17 y **el 28% en 2025-26**.

Periodo completo 2014 → 2026-10, como referencia (incluye datos de desarrollo): 246 operaciones, PF 2,18,
CAGR +53%, máx. DD −44%, Sharpe 1,17, frente a +44%, −84% y 0,88 de comprar y mantener. Gana en 11 de 13 años;
pierde en 2018 (−3%) y 2025 (−22%).

### Pruebas contra el azar

- **Las 154 operaciones fuera de muestra** (validación y ambas reservas): +2,8% de media por operación,
  **t = 3,0**. En 300 simulaciones con entradas aleatorias del mismo régimen, mismo número de operaciones y
  las mismas salidas, ninguna iguala la suma de retornos (p < 0,003).
- **Por tramos, contra entradas aleatorias** (Sharpe): desarrollo p = 0,03, validación p = 0,38,
  2014-17 p = 0,05, 2025-26 p = 0,50. Gran parte del resultado viene de la estructura de la estrategia (filtro
  de tendencia más trailing stop), que ya es rentable con entradas al azar. El momento de la ruptura añade
  valor claro en 2014-2022, pero no en 2023-2026.
- **2025-26 frente a la historia:** en un remuestreo de 42 operaciones tomadas de la distribución previa, solo
  el 1,1% de las veces sale una media tan mala. Es más probable un deterioro de la ventaja que una mala racha
  normal.

## Veredicto

- **La Failure Swing original no tiene arreglo en BTC:** su premisa está refutada por los datos.
- **La versión de ruptura sobre los mismos niveles tiene una ventaja real a largo plazo.** Es significativa
  fuera de muestra (t = 3,0 en 154 operaciones) y consistente en un régimen que no se usó para diseñarla
  (2014-17).
- **No cumple todos los criterios fijados de antemano.** Pierde en la reserva más reciente (2025-26), sus
  vecinas también, y ese tramo es estadísticamente anómalo frente a su historia. No se puede afirmar que sea
  rentable *hoy*.
- **En años alcistas no supera a comprar y mantener** (2017, 2019-2021, 2023-24). Su valor está en el
  drawdown, que es la mitad.
- **Ya no queda ningún dato de BTC sin usar.** Seguir ajustando con estos datos sería sobreajuste. La única
  prueba limpia que queda es el forward test con datos nuevos, o probarla en otros activos.

### Variantes probadas en total

1.728 + 384 + 1 (iteraciones 1-2), más el estudio de eventos (360 celdas), más 320 (iteración 3), más 54
vecinas. Solo una configuración llegó a las reservas.

### Cómo reproducirlo

```bash
python3 prepare_data.py                     # min.npz y min_full.npz
python3 dev_grid.py && python3 dev_grid2.py # iteraciones 1-2 (crea data/bars_full.pkl)
python3 cand.py                             # candidata de la iteración 2 frente al azar
python3 event.py && python3 bo_grid.py      # estudio de eventos e iteración 3
python3 final.py && python3 final_tests.py  # validación, reservas y pruebas contra el azar
```
