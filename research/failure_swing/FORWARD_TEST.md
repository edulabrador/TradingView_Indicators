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
