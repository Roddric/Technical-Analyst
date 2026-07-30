"""
price_cache.py
==============
Thin on-disk cache of normalized daily OHLCV fetched via akshare (A-share / HK /
US, routed by symbol shape). Cache survives across runs and pins each ticker's
snapshot. Successful fetches are cached to ./price_cache/<ticker>.csv; failed
fetches are NOT cached (so a later run retries only the still-missing tickers).

Contract: DatetimeIndex (naive, normalized) named "Date"; lowercase columns
open/high/low/close/volume; auto-adjusted prices.
"""

from __future__ import annotations

import os
import re
import tempfile
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "price_cache")


def _safe(tkr: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", tkr)


def _path(tkr: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{_safe(tkr)}.csv")


_ASHARE_COLS = {"日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume"}


def _fetch_akshare(tkr: str) -> pd.DataFrame | None:
    """Fetch full daily history via akshare, routed by symbol shape:
      - 6 digits            -> A-share  (stock_zh_a_hist, qfq-adjusted)
      - <=5 digits          -> Hong Kong (stock_hk_daily, qfq-adjusted)
      - otherwise (letters) -> US        (stock_us_daily)
    Symbols may carry a market suffix (600519.SH, 00700.HK, AAPL.US) — it is
    stripped. Returns the normalized lowercase-OHLCV frame the rest of the code
    expects, or None on any failure."""
    import akshare as ak

    sym = tkr.strip().upper()
    for suf in (".SH", ".SS", ".SZ", ".HK", ".US", ".O", ".N"):
        if sym.endswith(suf):
            sym = sym[: -len(suf)]
            break

    try:
        if sym.isdigit() and len(sym) == 6:                       # A-share
            raw = ak.stock_zh_a_hist(symbol=sym, period="daily", adjust="qfq")
            df = raw.rename(columns=_ASHARE_COLS)
        elif sym.isdigit() and len(sym) <= 5:                     # Hong Kong
            df = ak.stock_hk_daily(symbol=sym.zfill(5), adjust="qfq")
        else:                                                     # US
            df = ak.stock_us_daily(symbol=sym, adjust="qfq")
    except Exception:  # noqa: BLE001 — any fetch/parse error is a miss
        return None
    if df is None or len(df) == 0:
        return None

    df = df.rename(columns=str.lower)
    need = ["open", "high", "low", "close", "volume"]
    if "date" not in df.columns or any(c not in df.columns for c in need):
        return None
    d = pd.to_datetime(df["date"], errors="coerce")
    if getattr(d.dt, "tz", None) is not None:
        d = d.dt.tz_localize(None)
    out = df[need].copy()
    out.index = d.dt.normalize()
    out.index.name = "Date"
    for c in need:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(how="all").sort_index()


def _fetch_yf(tkr: str) -> pd.DataFrame | None:
    """Fallback fetch via yfinance for Yahoo-style symbols akshare can't route
    (e.g. 000660.KS, KRW=X, SKHY). Normalized to the same contract: naive
    DatetimeIndex named 'Date', lowercase OHLCV, auto-adjusted."""
    try:
        import yfinance as yf
        df = yf.download(tkr, period="max", auto_adjust=True, progress=False)
        if df is None or len(df) == 0:
            # Yahoo returns an EMPTY frame — not an error — for some live symbols
            # on period="max" (e.g. 7203.T), while a bounded window succeeds.
            # Without this fallback a tradeable symbol is indistinguishable from a
            # delisted one downstream, and the pair is dropped silently.
            df = yf.download(tkr, period="10y", auto_adjust=True, progress=False)
    except Exception:  # noqa: BLE001 — any fetch/parse error is a miss
        return None
    if df is None or len(df) == 0:
        return None
    df = df.copy()
    # yfinance may return MultiIndex columns (field, ticker) for a single symbol.
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df.rename(columns=str.lower)
    need = ["open", "high", "low", "close", "volume"]
    for c in need:
        if c not in df.columns:
            df[c] = float("nan")               # e.g. FX series have no volume
    idx = pd.to_datetime(df.index, errors="coerce")
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    out = df[need].copy()
    out.index = idx.normalize()
    out.index.name = "Date"
    for c in need:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna(how="all").sort_index()


def _fetch(tkr: str) -> pd.DataFrame | None:
    """akshare first (A-share/HK/US), then yfinance for Yahoo-style symbols."""
    df = _fetch_akshare(tkr)
    if df is not None and len(df) > 0:
        return df
    return _fetch_yf(tkr)


def load(tkr: str) -> pd.DataFrame | None:
    """Return cached normalized OHLCV if present, else fetch + cache."""
    path = _path(tkr)
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    df = _fetch(tkr)
    if df is not None and len(df) > 0:
        df.to_csv(path)
    return df


def refresh(tkr: str) -> pd.DataFrame | None:
    """Fetch and atomically replace a ticker's pinned snapshot.

    Normal reads remain pinned through :func:`load`; callers must opt into a
    refresh explicitly.  A failed or stale fetch never destroys a usable cache:
    the old CSV is left untouched and ``None`` is returned.
    """
    path = _path(tkr)
    current = None
    if os.path.exists(path):
        current = pd.read_csv(path, index_col=0, parse_dates=True)

    fresh = _fetch(tkr)
    if fresh is None or len(fresh) == 0:
        return None
    if current is not None and len(current):
        current_last = pd.Timestamp(current.index.max())
        fresh_last = pd.Timestamp(fresh.index.max())
        if fresh_last < current_last:
            return None

    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{_safe(tkr)}.", suffix=".csv.tmp", dir=CACHE_DIR)
    os.close(fd)
    try:
        fresh.to_csv(tmp_path)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return fresh


def prime(tickers, sleep_s: float = 4.0) -> dict:
    """Fetch any not-yet-cached tickers, spacing requests to dodge rate limits.
    Returns {ticker: rows or None}."""
    status = {}
    for tkr in tickers:
        path = _path(tkr)
        if os.path.exists(path):
            df = load(tkr)
            status[tkr] = len(df) if df is not None else None
            print(f"  cached  {tkr:<11} rows={status[tkr]}")
            continue
        df = _fetch(tkr)
        if df is not None and len(df) > 0:
            df.to_csv(path)
            status[tkr] = len(df)
            print(f"  fetched {tkr:<11} rows={len(df)}")
        else:
            status[tkr] = None
            print(f"  FAILED  {tkr:<11} (will retry next run)")
        time.sleep(sleep_s)     # be gentle with the data source
    return status


if __name__ == "__main__":
    from pandasta_data import TRADABLE   # deferred: pandasta_data imports us
    print("Priming price cache (spaced requests) ...")
    st = prime(TRADABLE)
    missing = [t for t, v in st.items() if v is None]
    print(f"\nCached {sum(1 for v in st.values() if v)}/{len(st)}. "
          f"Missing: {missing if missing else 'none'}")
