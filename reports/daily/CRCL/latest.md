# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-07-30T07:45:34.843303+00:00
- Latest daily market bar: 2026-07-29
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **61.36**, versus a 2026-01-28–2026-07-29 range of 49.90–140.00. It is -56.17% from the period high and 22.97% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 64.26 / 79.53 / 90.41.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 66.35 / 76.13; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-06-30).

## 3. Momentum

- RSI(14): **41.07** (neutral); divergence **bullish**.
- MACD / signal / histogram: -4.0289 / -4.9930 / 0.9641.
- MACD state: **bullish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 59.11 / 64.26 / 69.41; %B 0.219.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.3983 (8.80% of price); expected daily range 5.40.

## 5. Volume

- OBV trend **rising**, strength **moderate**.
- Price confirmation: **False**; divergence **bullish_accumulation**.

## 6. Key levels

- Quick 60-bar support / resistance: 58.68 / 140.00.
- Distance to support / resistance: 4.37% / 128.16%; range reward:risk 29.34.

**Confirmed supports**

- 59.97 (4 touches; last 2026-07-24; -2.27% from price)
- 55.31 (1 touches; last 2026-02-12; -9.86% from price)
- 49.90 (1 touches; last 2026-02-05; -18.68% from price)

**Confirmed resistances**

- 64.92 (1 touches; last 2025-11-20; 5.80% from price)
- 76.08 (8 touches; last 2026-07-21; 23.99% from price)
- 84.44 (2 touches; last 2026-04-09; 37.61% from price)

Dominant swing: **down**, 189.92 (2025-08-12) to 49.90 (2026-02-05). Nearest Fibonacci level is 0.236 at 82.94 (35.17% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bearish** while MACD is **bullish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **bullish** and price/OBV confirmation is **False**.
- Bollinger squeeze is **True** while ATR-based volatility is **contracting**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 61.36,
  "stop": 61.36,
  "target": 61.36,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

No prior report was found inside the seven-day window. This is the baseline; comparisons will populate automatically on later runs.

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 0 directional report(s) have matured, 0 are pending, and 1 were honest abstentions.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
