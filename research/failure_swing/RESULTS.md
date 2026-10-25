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
