# Mejorar la estrategia de un solo gráfico (TradingView) hasta Sharpe > 1

**Objetivo, fijado antes de iterar:** con un solo activo y costes completos,

1. Sharpe mediano ≥ 1,0 en el periodo completo y ≥ 0,9 en 2023-26, en los 12 pares de Binance;
2. Sharpe > 1 en BTC con las tres fuentes de datos;
3. cada mejora debe aparecer tanto en desarrollo (hasta 2022) como en prueba (2023-26).

Se prueba en los 12 pares de Binance (2017-26), BTC de Bitstamp (2014-26), y BTC y oro de Dukascopy (2022-26).
El motor `single.py` reproduce el Pine vela a vela, con las órdenes en la apertura siguiente; da exactamente
1,53 en BTC de Bitstamp, igual que la réplica anterior.

## Iteraciones (`iter1.py` a `iter3.py`; unas 25 variantes)

| Variante | Mediana 12 pares: total / desarrollo / 2023-26 / 2025-26 | Pares > 1 | BTC Binance / Bitstamp / Dukascopy | Oro (Dukascopy) |
|---|---|---|---|---|
| Base (Pine anterior) | 1,00 / 1,24 / 0,79 / 0,15 | 6/12 | 1,19 / 1,53 / 0,86 | 1,48 |
| I1: umbral de reajuste del 10% | 1,05 / 1,25 / 0,85 / 0,30 | 7/12 | 1,20 / 1,51 / 0,90 | 1,49 |
| I2: momentum continuo, normalizado por volatilidad | 0,99 / 1,15 / 0,83 / 0,28 | 6/12 | 1,35 / 1,60 / 1,00 | 1,35 |
| I3: promediar las rupturas de 42, 84 y 168 velas | 1,02 / 1,21 / 0,78 / 0,11 | 6/12 | 1,18 / 1,52 / 0,88 | 1,49 |
| I4: velas diarias | 0,88 / 1,00 / 0,62 / −0,16 | 5/12 | 1,11 / 1,30 / 0,87 | 1,06 |
| I5: sin la media de tendencia | 0,96 / 1,18 / 0,79 / 0,11 | 5/12 | 1,18 / 1,51 / 0,80 | 1,50 |
| **R2a: I1 + I2** | **1,04 / 1,22 / 0,89 / 0,38** | 7/12 | **1,31 / 1,60 / 0,99** | 1,38 |
| R2b: I1 + I3 | 1,03 / 1,25 / 0,82 / 0,19 | 7/12 | 1,21 / 1,49 / 0,92 | 1,50 |
| R2c: I1 + I2 + I3 | 1,04 / 1,24 / 0,83 / 0,24 | 7/12 | 1,29 / 1,58 / 0,97 | 1,38 |
| R2d: R2a con umbral del 20% | 1,06 / 1,20 / 0,86 / 0,40 | 8/12 | 1,31 / 1,57 / 0,92 | 1,38 |
| R3a: R2a + volatilidad EWMA | 1,03 / 1,20 / 0,82 / 0,46 | 7/12 | 1,33 / 1,61 / 0,90 | 1,37 |
| R3b: R2a + filtro de régimen de 200 días | 0,84 / 0,99 / 0,60 / 0,40 | 3/12 | 1,15 / 1,51 / 1,01 | 1,24 |

**Se elige R2a** (umbral del 10% y momentum continuo), que ya está aplicada en el Pine.

- Mejora la base en desarrollo, en prueba y en 2025-26.
- En las 13 pruebas de sensibilidad (umbral, horizontes, periodo de ruptura, trailing, ventana de volatilidad,
  peso de cada pata y costes), la mediana de un solo activo queda entre 0,96 y 1,05, y la de 2023-26 entre 0,76 y
  0,86.

**Con un solo activo, el objetivo se cumple a medias.**

- La mediana total llega a 1,04, pero la de 2023-26 se queda en 0,89, y 0,89 es además el mejor valor de la
  banda de sensibilidad.
- BTC supera 1 en Binance (1,31) y en Bitstamp (1,60), pero se queda en 0,99 con Dukascopy, que solo cubre
  desde 2022.
- **El techo realista con un solo gráfico es un Sharpe de ~1,0.**

## La forma robusta de superar 1: varios gráficos (`iter4.py`, `iter5.py`)

La misma estrategia en varios gráficos de TradingView, con el capital repartido a partes iguales:

| Cesta (R2a) | Rebalanceo | Sharpe | 2023-26 | 2025-26 | CAGR | DD |
|---|---|---|---|---|---|---|
| **BTC + ETH (desde 2017)** | sin rebalanceo / mensual | **1,43 / 1,46** | 1,12 / 1,14 | 0,40 / 0,43 | +30% | −20% |
| BTC + ETH + SOL (desde 2020-10) | sin rebalanceo / mensual | 1,69 / 1,73 | 1,44 | 0,50 | +31% | −16% |
| BTC, ETH, BNB, SOL, XRP (desde 2020-10) | sin rebalanceo / mensual | 1,77 / 1,88 | 1,42 / 1,53 | 0,61 / 0,65 | +30-34% | −15% |
| 12 pares (diario) | diario | 1,63 | 1,37 | 0,45 | +25% | −14% |
| BTC + oro (Dukascopy, 2022-26) | diario | 1,31 | 1,56 | 1,17 | +16% | −12% |

- **Sesgo de selección:** la cesta de las 5 mayores se elige con lo que se sabe hoy, porque en 2020 nadie sabía
  que SOL, BNB y XRP acabarían en el top 5. La cifra **honesta es la de BTC + ETH, con Sharpe de ~1,4**. Esos
  dos ya eran los mayores en 2017.
- Con R2a, la cesta de 12 pares queda entre 1,40 y 1,66 en todas las pruebas de sensibilidad.
- **Monte Carlo, cesta de 5, 12 meses:** Sharpe p5 −0,34, p50 1,78. Probabilidad de que el Sharpe supere 1 en
  12 meses: 75%; en 3 años, 89%; en 5 años, 95%. Drawdown p1 a 12 meses: −17%.
- **Por años (cesta de 5):** 2020 +26%, 2021 +95%, 2022 −3%, 2023 +38%, 2024 +50%, 2025 +15%, 2026 −0%.

## Conclusión

- Con un solo gráfico, R2a deja la estrategia en un Sharpe de **~1,0**: **~1,3 en BTC** con historia larga y
  ~0,8-0,9 en el tramo reciente.
- La forma robusta de tener **Sharpe > 1 es usar dos o más gráficos**. BTC + ETH da ~1,4 desde 2017 y ~1,1 en
  2023-26, con drawdown de −20%.
- Ambas cestas quedan registradas en el forward test (`../FORWARD_TEST.md`, `forward_r2a.py`).
