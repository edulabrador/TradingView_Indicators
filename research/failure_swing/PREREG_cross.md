Cross-asset test, written before running (2026-10-25).
Frozen rules: 4h bars, S/R period 84, chandelier trail 4 ATR(14), trend SMA 50 days, long+short, reverse on opposite signal,
100% equity, cost 0.15%/side. No parameter changes after seeing results.
Assets: Binance spot ETH SOL BNB XRP LTC ADA DOGE LINK TRX AVAX DOT (BTCUSDT reported apart, not independent of the Bitstamp BTC work).
Window: from first bar + 60 days warm-up to 2026-10-24. Also report 2025-01 -> 2026-10 separately.
Success: (1) >= 8 of 11 assets with CAGR > 0 and PF > 1 over full window; (2) pooled random-entry test p < 0.05
(same regime eligibility, same trade count per side, same exits, 200 draws per asset, statistic = sum of trade returns,
pooled by summing across assets per draw); (3) median per-asset PF > 1.2.
