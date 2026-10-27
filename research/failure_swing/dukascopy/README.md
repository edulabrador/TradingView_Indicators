# Backtest y robustez con datos de Dukascopy

## Acceso a los datos

- **MCP:** existe un servidor MCP de Dukascopy hecho por terceros ([listado en Glama](https://glama.ai/mcp/servers/dt4w4y97py)),
  no oficial. Descarga ticks y velas de 1 minuto del feed público de Dukascopy. No está en el directorio de
  conectores de claude.ai.
- **Red:** este entorno en la nube bloquea `datafeed.dukascopy.com`, así que ni el MCP ni una descarga directa
  funcionan aquí. Para habilitarlo hay que añadir ese dominio en *Network access → Allowed domains* del entorno
  (https://code.claude.com/docs/en/cloud-environments#network-access).
- **Fuente usada:** velas BID de 1 minuto de Dukascopy para BTCUSD y XAUUSD, de 2022-01 a 2026-08, descargadas
  con `dukascopy-node` y publicadas en [meffyou226-oss/Meffs](https://github.com/meffyou226-oss/Meffs)
  (`prepare_duka.sh`).
- **Limpieza:** uno de los ficheros de oro (2023-09) trae marcas de conflicto de git, así que se descartan las
  líneas no numéricas y los duplicados. En el oro se eliminan además las velas sin movimiento (fines de semana
  rellenados).
- **Calidad de BTC:** frente a Binance y Bitstamp, correlación de retornos de 4h de 0,998 y diferencia mediana
  de precio del 0,07-0,08%.
- **Costes:** 0,15% por lado en BTC. En el oro, 0,03% por lado (spread típico de un CFD), con prueba también al
  0,15%.

## Backtests (2022-05 → 2026-08, 4h; `duka_bt.py`)

| Estrategia | BTC | Oro (XAU) |
|---|---|---|
| Comprar y mantener | Sharpe 0,60, CAGR +18%, DD −60% | Sharpe 1,27, CAGR +23%, DD −28% |
| Failure Swing original v3 / v6 | PF 0,60 / 0,79, CAGR −24% / −14% | 10 operaciones, CAGR ≈ 0% |
| Ruptura S/R (largos y cortos) | Sharpe 0,48, CAGR +11%, DD −46% | Sharpe 1,19, CAGR +14%, DD −12% |
| **Breakout Momentum Vol-Target (Pine)** | **Sharpe 0,86, CAGR +16%, DD −21%** | **Sharpe 1,48, CAGR +16%, DD −14%** (1,22 con 0,15%) |
| **BTC + XAU a partes iguales** | **Sharpe 1,25, CAGR +16%, DD −12%** | |

Año a año de la versión Pine:

- BTC: 2022 −14%, 2023 +55%, 2024 +45%, 2025 +1%, 2026 −2%.
- Oro: 2022 −2%, 2023 +6%, 2024 +14%, 2025 +39%, 2026 +16%.
- La correlación diaria entre ambas es de 0,08.

## Robustez (`duka_robust.py`)

1. **La fuente de datos no importa.** En la misma ventana, BTC da Sharpe 0,85 con Dukascopy, 0,83 con Binance y
   0,82 con Bitstamp.
2. **Monte Carlo** (bloques de 30 días, 10.000 trayectorias):

   | Cartera | 12 meses: Sharpe p5 / p50, P(perder), DD p5 | 3 años: Sharpe p5 / p50, P(perder), DD p1 |
   |---|---|---|
   | BTC | −1,30 / 0,81, 27%, −25% | −0,24 / 0,87, 12%, −46% |
   | XAU | 0,00 / 1,53, 6%, −13% | 0,67 / 1,53, 0%, −20% |
   | BTC + XAU | −0,56 / 1,22, 14%, −14% | 0,30 / 1,27, 2%, −24% |

3. **Parámetros** (300 configuraciones al azar): el 100% tiene Sharpe positivo. BTC queda en p5 0,64 / p50 0,83;
   el oro en 1,23 / 1,46; la cartera en 1,05 / 1,24. La configuración elegida está en el centro de la
   distribución, no es un pico.
4. **Ejecución** (15% de órdenes perdidas, deslizamiento extra y la mitad de las simulaciones con 4h de retraso):
   Sharpe mediano de 0,69-0,73 en BTC, 1,35-1,42 en el oro y 1,08-1,09 en la cartera.
5. **Precios sintéticos:**
   - **BTC:** al barajar las velas, el Sharpe cae a 0,12 (P = 0,04). La ventaja depende del momentum.
   - **Oro:** al barajar, sigue dando 0,95 (P = 0,16). Gran parte del resultado se explica por la fuerte
     tendencia alcista del oro entre 2022 y 2026, no por la lógica de la estrategia. **No hay pruebas de una
     ventaja propia en el oro**, más allá de recortar el drawdown a la mitad frente a comprar y mantener.
6. **Walk-forward** (2 años de entrenamiento, 6 meses de prueba, 27 configuraciones):
   - BTC desde 2024-05: reoptimizado 0,79 frente a 0,43 de la configuración fija. En BTC, la configuración fija
     ha ido floja en el último tramo.
   - Oro desde 2024-06: 1,92 frente a 1,89.
   - Es lo contrario de lo que salió en la cartera de 12 criptos, donde reoptimizar empeoraba. La evidencia sobre
     reoptimizar es mixta.
7. **PSR**, la probabilidad de que el Sharpe real sea mayor que cero: BTC 0,964, oro 0,998 y cartera 0,996.

## Conclusión

- Los datos de Dukascopy **confirman** la estrategia en BTC: Sharpe de ~0,85 desde 2022, frente a 0,60 de
  comprar y mantener, con la tercera parte de drawdown.
- En el oro funciona, pero **su ventaja en el oro no está demostrada**: casi todo viene de la tendencia del
  periodo.
- La combinación BTC + oro es la más estable (Sharpe 1,25, DD −12%), sobre todo por la diversificación
  (correlación 0,08).
- **Forward test:** estos datos acaban en 2026-08, así que no aportan nada posterior a lo ya visto. El forward
  test real sigue siendo el registrado en `../FORWARD_TEST.md`, con datos de Binance.
