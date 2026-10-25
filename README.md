# TradingView Indicators and Strategies (pinescript)

###### GitHub: https://github.com/Heavy91/TradingView_Indicators

###### TradingView: https://www.tradingview.com/u/Heavy91/#published-scripts

## If you like my work, you can support me with a donation:
**€:** http://pinescripts.fetchapp.com/sell/d15d4740

**$:** http://pinescripts.fetchapp.com/sell/0f9153a5

**BTC:** bc1q8e4wav3t55plp6ar0xc7gh4uqrzlxc7g97ywrg

**LTC:** ltc1qagcys3pyluke3xdlq94qx8p7fd3z3mj2w32grs

-------------------------------------------------------------------------------------

## Indicators:

- **RSI MultiTimeframe:**
  Plots 3 RSI (Weekly, Daily, 4h) at the same time, regardless of the Chart Timeframe.
  Highlights in green (or red) if all RSI are oversold (or overbought).
  Can trigger custom oversold and overbought alerts.
  ![alt text](https://github.com/Heavy91/TradingView_Indicators/blob/master/%5Bpreview%5D%20RSI%20MultiTimeframe%20I.png)
  
- **Volume Supply and Demand Zones:**
  Draws supply and demand zones based on 3 different volume threshold parameters.
  The timeframe of the script is fixed (you can change it in the options), 
  e.g. it is possible to keep Daily S/D zones while looking at 1h chart.
  ![alt text](https://github.com/Heavy91/TradingView_Indicators/blob/master/%5Bpreview%5D%20Volume%20Supply%20and%20Demand%20Zones%20I.png)
  
- **MultiAverages MultiTimeframe:**
  Plots different kinds of averages ( EMA , SMA , SMMA , WMA , VWMA ) referred to a fixed timeframe, indipendent from   the one that you are watching, e.g. plot daily EMA on the 1h chart.
  Highlights the crossing of averages.
  ![alt text](https://github.com/Heavy91/TradingView_Indicators/blob/master/%5Bpreview%5D%20MultiAverages%20MultiTimeframe%20I.png)
  

## Strategies:

- **Failure Swing (stop hunting):**
  This strategy is a first attempt to countertrade the false break of a key support/resistance.
  If a candle breaks the level, but it comes back before the close, it will trigger an order.
  The Stop Loss is in %, the Take Profit is near the EMA.
  The *volatility filter* is used to block new orders when the price is near the EMA.
  The *volatility adjustment* coefficients calibrate Stop Loss and Take Profit values according to the current volatility.
  ![alt text](https://github.com/Heavy91/TradingView_Indicators/blob/master/%5Bpreview%5D%20Failure%20Swing%20S.png)
  
  A Pine Script v6 port is in *Failure Swing (stop hunting) Strategy v6.pine*: Stop Loss and Take Profit are real
  stop/limit orders and entries can be restricted to the side of the EMA. A backtest on BTC/USD (2018-2026,
  1-minute intrabar resolution) found it unprofitable on every timeframe; see
  [research/failure_swing/RESULTS.md](research/failure_swing/RESULTS.md).

- **Support/Resistance Breakout (v6):**
  Same 84-bar support/resistance levels as Failure Swing, but it trades the breakout instead of its failure,
  with a 50-day SMA trend filter and an ATR trailing stop (4h bars). Out of sample on BTC/USD it was profitable
  in 2014-2017 and 2023-2024 (154 trades, t = 3.0) but lost in 2025-2026; see the same research report.
  
