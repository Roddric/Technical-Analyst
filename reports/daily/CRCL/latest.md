# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-24T00:53:51.242948+00:00
- Latest daily market bar: 2026-10-23
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **85.91**, versus a 2026-04-27–2026-10-23 range of 57.84–140.00. It is -38.64% from the period high and 48.53% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 83.79 / 86.96 / 86.16.
- Price position: SMA20 **above**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 85.17 / 84.43; stack **bullish**.
- Latest SMA50/200 event: golden_cross (2026-10-21).

## 3. Momentum

- RSI(14): **50.96** (neutral); divergence **none**.
- MACD / signal / histogram: -0.0448 / -0.4955 / 0.4507.
- MACD state: **bullish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 78.88 / 83.79 / 88.70; %B 0.716.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.6617 (6.59% of price); expected daily range 5.66.

## 5. Volume

- OBV trend **falling**, strength **weak**.
- Price confirmation: **False**; divergence **bearish_distribution**.

## 6. Key levels

- Quick 60-bar support / resistance: 57.84 / 103.28.
- Distance to support / resistance: 32.67% / 20.22%; range reward:risk 0.62.

**Confirmed supports**

- 76.41 (12 touches; last 2026-10-15; -11.06% from price)
- 64.92 (1 touches; last 2025-11-20; -24.43% from price)
- 58.84 (6 touches; last 2026-08-03; -31.51% from price)

**Confirmed resistances**

- 87.89 (12 touches; last 2026-10-15; 2.30% from price)
- 101.32 (8 touches; last 2026-09-21; 17.94% from price)
- 111.20 (1 touches; last 2026-04-17; 29.44% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.618 at 84.32 (-1.85% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bullish** while MACD is **bullish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
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
  "entry": 85.91,
  "stop": 85.91,
  "target": 85.91,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-16 through 2026-10-23, price changed **4.49%**. RSI ranged from 45.98 to 55.70. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-16 | 82.22 | 46.93 | bullish | bearish | flat | 0.000 |
| 2026-10-19 | 81.37 | 45.98 | bullish | bearish | flat | 0.000 |
| 2026-10-20 | 85.87 | 51.53 | bullish | bearish | flat | 0.000 |
| 2026-10-21 | 89.71 | 55.70 | bullish | bullish | flat | 0.000 |
| 2026-10-22 | 86.62 | 51.83 | bullish | bullish | flat | 0.000 |
| 2026-10-23 | 85.91 | 50.96 | bullish | bullish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 48 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
