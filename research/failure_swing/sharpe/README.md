# ¿Se puede llegar a Sharpe 2 de forma robusta?

**Respuesta: no con los datos disponibles.** El techo robusto está en un **Sharpe de ~1,1-1,25**. Cualquier
configuración que diera 2 en este histórico sería sobreoptimización.

## Reglas del ejercicio

- Solo palancas respaldadas por la literatura y con parámetros estándar fijados a priori: dimensionar por
  volatilidad, repartir el riesgo a partes iguales, combinar horizontes, añadir fuentes de retorno poco
  correlacionadas y diversificar en otras clases de activo.
- Costes del 0,15% por lado en entradas, salidas, reajustes de tamaño y en el ajuste implícito de mantener una
  exposición constante.
- Siempre se informa por separado del desarrollo (hasta 2022), la prueba (2023-26) y 2025-26.
- Unas 30 carteras evaluadas en total.

Universo: los 12 pares de Binance de 2017-10 a 2026-10. Sharpe calculado con datos diarios; "±" es el error
estándar.

| Iteración | Cartera | Sharpe total | Desarrollo | 2023-26 | 2025-26 | CAGR | DD |
|---|---|---|---|---|---|---|---|
| base | Capital a partes iguales, exposición constante | 0,61 ± 0,36 | 0,78 | 0,27 | −0,10 | +20% | −47% |
| 1 | Riesgo a partes iguales (volatilidad de 30 días) | 0,95 ± 0,40 | 1,14 | 0,65 | 0,31 | +25% | −21% |
| 2 | Más un promedio de 4 horizontes y 2 trailings | 0,96 ± 0,40 | 1,18 | 0,59 | 0,30 | +22% | −20% |
| 3 | Momentum entre activos (neutral al mercado), solo | 0,39 ± 0,36 | 0,78 | −0,05 | −0,64 | +5% | −24% |
| 3 | Tendencia + momentum entre activos + cesta comprada, sin costes de reponderación | 1,42 | 1,78 | 0,99 | −0,28 | | |
| **4 · A** | **Tendencia con riesgo a partes iguales y objetivo de volatilidad del 25% en la cartera** | **1,14 ± 0,43** | 1,36 | 0,82 | 0,44 | +39% | −28% |
| 4 · B | A más una cesta comprada dimensionada por volatilidad, riesgo a partes iguales | 1,24 ± 0,44 | 1,41 | 1,00 | 0,12 | +40% | −38% |
| 5 | Divisas y oro (11 pares + XAU, 2013-22) con las reglas congeladas | −0,18 ± 0,33 | | | | −1% | −20% |
| 5 | Cripto + divisas, riesgo a partes iguales (2017-12 a 2022-03) | 0,62 frente a 1,28 de solo cripto | | | | | |

## Lo que funciona y lo que no

- **Funciona:** dimensionar por volatilidad, tanto por activo como en la cartera, sube el Sharpe de 0,61 a 1,14
  y reduce el drawdown del −47% al −28%. Es robusto: cambiando una a una las ventanas de volatilidad
  (15-90 días), el tope de apalancamiento (1,5-5x), los costes (0,05-0,25%) y los parámetros de la ruptura
  (42-168 / 3-5 ATR / SMA de 50-100 días), el Sharpe se queda siempre entre 1,03 y 1,20.
- **No aporta Sharpe:** promediar horizontes, porque los subsistemas tienen correlación 0,99. Sí reduce el
  riesgo de haber elegido mal el parámetro.
- **No funciona:** el momentum entre activos, que no gana desde 2023, ni diversificar en divisas y oro, donde
  estas reglas pierden.
- **Funciona con matices:** la cesta comprada (B) sube el Sharpe a 1,24 gracias a una correlación de −0,14,
  pero depende de que la cripto siga dando prima a largo plazo, y en 2025-26 empeora.
- **La mejor cifra de desarrollo** (1,78, en la iteración 3) cayó a 0,99 en 2023-26 y a −0,28 en 2025-26. Es
  el patrón típico de la sobreoptimización.

## Por qué no se puede afirmar un Sharpe de 2

- Con 9 años de datos, el error estándar es de ±0,43. Un Sharpe estimado de 1,14 tiene un intervalo de
  confianza del 95% de aproximadamente [0,3; 2,0]. Un backtest de 2,0 no se distinguiría de uno de 1,5.
- El único camino creíble hacia 2 es sumar fuentes de retorno con correlación baja y Sharpe propio de ~1. Eso
  requiere datos que aquí no hay: financiación de futuros y basis (carry), datos on-chain, flujo de órdenes, o
  más clases de activo con su propio modelo y datos posteriores a 2022.

## Recomendación

Usa la **cartera A**: la estrategia de ruptura en los 12 pares con riesgo a partes iguales y objetivo de
volatilidad del 25%. Pasa de Sharpe 0,90 a 1,14 con todos los costes y su drawdown de −28% es menos de la mitad.
Si la entra al forward test, debe hacerlo con sus propios criterios, porque es una variante nueva.
