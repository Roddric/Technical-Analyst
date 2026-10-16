# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-16T00:32:12.617513+00:00
- Latest daily market bar: 2026-10-15
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **86.97**, versus a 2026-04-17–2026-10-15 range of 57.84–140.00. It is -37.88% from the period high and 50.36% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 85.93 / 85.02 / 86.07.
- Price position: SMA20 **above**, SMA50 **above**, SMA200 **above**.
- EMA20 / EMA50: 84.82 / 84.16; stack **bullish**.
- Latest SMA50/200 event: death_cross (2026-06-30).

## 3. Momentum

- RSI(14): **52.50** (neutral); divergence **none**.
- MACD / signal / histogram: -0.9231 / -0.7023 / -0.2208.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 76.57 / 85.93 / 95.30; %B 0.555.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.8764 (6.76% of price); expected daily range 5.88.

## 5. Volume

- OBV trend **rising**, strength **weak**.
- Price confirmation: **False**; divergence **bullish_accumulation**.

## 6. Key levels

- Quick 60-bar support / resistance: 57.84 / 103.28.
- Distance to support / resistance: 33.49% / 18.75%; range reward:risk 0.56.

**Confirmed supports**

- 76.52 (11 touches; last 2026-10-08; -12.02% from price)
- 64.92 (1 touches; last 2025-11-20; -25.35% from price)
- 58.84 (6 touches; last 2026-08-03; -32.34% from price)

**Confirmed resistances**

- 87.91 (11 touches; last 2026-10-09; 1.08% from price)
- 101.32 (8 touches; last 2026-09-21; 16.50% from price)
- 111.20 (1 touches; last 2026-04-17; 27.86% from price)

Dominant swing: **down**, 147.44 (2025-10-27) to 49.90 (2026-02-05). Nearest Fibonacci level is 0.382 at 87.16 (0.22% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bullish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **False**.
- Bollinger squeeze is **True** while ATR-based volatility is **contracting**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 86.97,
  "stop": 86.97,
  "target": 86.97,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-08 through 2026-10-15, price changed **7.58%**. RSI ranged from 42.61 to 52.50. Council state changed 3 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-08 | 80.84 | 43.78 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-09 | 84.51 | 48.82 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-12 | 83.87 | 48.01 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-13 | 84.27 | 48.59 | bullish | bearish | flat | 0.000 |
| 2026-10-14 | 79.55 | 42.61 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-15 | 86.97 | 52.50 | bullish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 10 directional report(s) have matured, 3 are pending, and 42 were honest abstentions.
Observed directional hit rate is 50.00% and mean signed forward return is -0.91%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
