# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-14T02:34:32.363568+00:00
- Latest daily market bar: 2026-11-13
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **62.20**, versus a 2026-05-18–2026-11-13 range of 57.84–118.85. It is -47.67% from the period high and 7.54% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 75.58 / 82.68 / 85.87.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 73.09 / 78.42; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **31.50** (neutral); divergence **none**.
- MACD / signal / histogram: -5.3370 / -4.0358 / -1.3012.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 59.07 / 75.58 / 92.09; %B 0.095.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.1168 (8.23% of price); expected daily range 5.12.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 60.56 / 103.28.
- Distance to support / resistance: 2.64% / 66.05%; range reward:risk 25.05.

**Confirmed supports**

- 58.84 (6 touches; last 2026-08-03; -5.40% from price)
- 49.90 (1 touches; last 2026-02-05; -19.77% from price)

**Confirmed resistances**

- 64.92 (1 touches; last 2025-11-20; 4.37% from price)
- 76.11 (14 touches; last 2026-11-04; 22.36% from price)
- 88.22 (13 touches; last 2026-10-21; 41.83% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (11.22% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bearish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **True**.
- Bollinger squeeze is **False** while ATR-based volatility is **expanding**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 62.2,
  "stop": 62.2,
  "target": 62.2,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-11-06 through 2026-11-13, price changed **-8.37%**. RSI ranged from 31.50 to 35.97. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-06 | 67.88 | 34.75 | bearish | bearish | flat | 0.000 |
| 2026-11-09 | 67.56 | 34.46 | bearish | bearish | flat | 0.000 |
| 2026-11-10 | 64.98 | 32.18 | bearish | bearish | flat | 0.000 |
| 2026-11-11 | 67.12 | 35.97 | bearish | bearish | flat | 0.000 |
| 2026-11-12 | 63.82 | 32.92 | bearish | bearish | flat | 0.000 |
| 2026-11-13 | 62.20 | 31.50 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 63 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
