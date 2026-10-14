# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-14T01:18:29.803869+00:00
- Latest daily market bar: 2026-10-13
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **84.27**, versus a 2026-04-15–2026-10-13 range of 57.84–140.00. It is -39.81% from the period high and 45.70% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 85.89 / 84.22 / 86.05.
- Price position: SMA20 **below**, SMA50 **above**, SMA200 **below**.
- EMA20 / EMA50: 85.13 / 84.23; stack **bullish**.
- Latest SMA50/200 event: death_cross (2026-06-30).

## 3. Momentum

- RSI(14): **48.59** (neutral); divergence **none**.
- MACD / signal / histogram: -0.9927 / -0.4854 / -0.5073.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 76.64 / 85.89 / 95.13; %B 0.413.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.3200 (6.31% of price); expected daily range 5.32.

## 5. Volume

- OBV trend **rising**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 57.84 / 103.28.
- Distance to support / resistance: 31.36% / 22.56%; range reward:risk 0.72.

**Confirmed supports**

- 76.52 (11 touches; last 2026-10-08; -9.20% from price)
- 64.92 (1 touches; last 2025-11-20; -22.96% from price)
- 58.84 (6 touches; last 2026-08-03; -30.18% from price)

**Confirmed resistances**

- 87.94 (10 touches; last 2026-10-02; 4.36% from price)
- 101.32 (8 touches; last 2026-09-21; 20.23% from price)
- 111.20 (1 touches; last 2026-04-17; 31.96% from price)

Dominant swing: **down**, 147.44 (2025-10-27) to 49.90 (2026-02-05). Nearest Fibonacci level is 0.382 at 87.16 (3.43% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bullish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **True**.
- Bollinger squeeze is **True** while ATR-based volatility is **contracting**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 84.27,
  "stop": 84.27,
  "target": 84.27,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-06 through 2026-10-13, price changed **0.17%**. RSI ranged from 43.78 to 48.82. Council state changed 1 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-06 | 84.13 | 47.39 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-07 | 80.84 | 43.78 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-08 | 80.84 | 43.78 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-09 | 84.51 | 48.82 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-12 | 83.87 | 48.01 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-13 | 84.27 | 48.59 | bullish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 8 directional report(s) have matured, 4 are pending, and 41 were honest abstentions.
Observed directional hit rate is 50.00% and mean signed forward return is -0.39%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
