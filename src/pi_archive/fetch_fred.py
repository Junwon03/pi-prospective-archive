"""FRED fetch — long-format raw records with vintage metadata.

common C11.2 raw.csv 스키마에 대응. API 키는 환경변수 FRED_API_KEY.
네트워크 없는 환경(테스트·재현)에서는 load_raw_csv로 대체.
"""
from __future__ import annotations

import datetime as dt
import os

import pandas as pd

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_series(series_id: str, api_key: str | None = None,
                 observation_start: str | None = None) -> pd.DataFrame:
    """FRED에서 한 시리즈 fetch → long-format DataFrame.

    columns: provider, series_id, observation_date, realtime_start,
             realtime_end, value, fetch_status, fetched_at_utc
    결측('.')은 value=NaN + fetch_status='missing_at_source'로 **그대로 기록**
    (raw 층은 그날 보인 상태의 박제 — common C10.2).
    """
    import requests  # 지연 import — 오프라인 테스트에서 불필요

    api_key = api_key or os.environ["FRED_API_KEY"]
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    if observation_start:
        params["observation_start"] = observation_start

    resp = requests.get(FRED_URL, params=params, timeout=60)
    resp.raise_for_status()
    obs = resp.json()["observations"]

    # unit: series 메타에서 조회 (common C11.2 raw schema). 실패해도 fetch는 진행.
    unit = None
    try:
        meta = requests.get(
            "https://api.stlouisfed.org/fred/series",
            params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
            timeout=30,
        )
        meta.raise_for_status()
        unit = meta.json()["seriess"][0].get("units_short")
    except Exception:
        pass

    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()
    rows = []
    for o in obs:
        missing = o["value"] in (".", "", None)
        rows.append({
            "provider": "FRED",
            "series_id": series_id,
            "observation_date": o["date"],
            "realtime_start": o.get("realtime_start"),
            "realtime_end": o.get("realtime_end"),
            "value": None if missing else float(o["value"]),
            "unit": unit,
            "fetch_status": "missing_at_source" if missing else "ok",
            "fetched_at_utc": fetched_at,
        })
    return pd.DataFrame(rows)


def raw_to_series(raw_long: pd.DataFrame, series_id: str) -> pd.Series:
    """long-format raw → 계산용 Series (index=observation_date).
    결측은 NaN 유지 — fill은 channels 모듈의 SPEC 규칙만 담당."""
    d = raw_long[raw_long["series_id"] == series_id].copy()
    d["observation_date"] = pd.to_datetime(d["observation_date"])
    s = d.set_index("observation_date")["value"].astype(float).sort_index()
    return s


def load_raw_csv(path: str) -> pd.DataFrame:
    """저장된 long-format raw.csv 로더 (재현·오프라인용)."""
    return pd.read_csv(path)
