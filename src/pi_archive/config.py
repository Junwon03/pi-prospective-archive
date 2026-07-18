"""SPEC-1.0-C-US configuration.

이 파일의 상수는 SPEC-1.0-C-US_v5.md의 frozen 정의와 1:1 대응한다.
SPEC 문서가 헌법이고 이 파일은 그 기계적 표현이다 — 여기 값을 바꾸는 것은
SPEC을 바꾸는 것과 동일하며, freeze 후에는 새 SPEC 버전 없이 변경 금지.

[TODO] 표시 값은 calibration 후 확정 (SPEC 체크리스트 참조).
"""

# ---------------------------------------------------------------- channels
# SPEC §1
FRED_SERIES = {
    "DFF": {"role": "rho_base", "freq": "daily"},
    "DCPF3M": {"role": "psi_spread_long", "freq": "daily"},
    "DTB3": {"role": "psi_spread_short", "freq": "daily"},
    "TOTBKCR": {"role": "omega_base", "freq": "weekly"},
}

# sensitivity 전용 (SPEC §1.1 — 기록만, primary 불변경)
SENSITIVITY_SERIES = {"DGS3MO": {"role": "psi_spread_short_alt", "freq": "daily"}}

# historical 재현 전용 (SPEC §1.2 — foundation 조합. 단종 시리즈, live 사용 금지)
REPRO_ONLY_SERIES = {"TEDRATE": {"role": "psi_repro", "freq": "daily"}}

# 변환 (SPEC §1): |Δ over 5 거래일 관측치| for rho, psi; omega = level
DELTA_TRADING_DAYS = 5

# ------------------------------------------------------------- fill rules
# SPEC §1.3 — 채널별 LOCF 한도 (calendar days). LOCF만 허용 (common C4.5 인과성).
FILL_LIMIT_CALENDAR_DAYS = {
    "DFF": 5,
    "DCPF3M": 5,
    "DTB3": 5,
    "DGS3MO": 5,
    "TEDRATE": 5,   # 재현 모드 전용
    "TOTBKCR": 14,  # 주간 시리즈: 주기 7일 + 발표 지연 여유
}

# ------------------------------------------------------------------ alert
# SPEC §3
SBAR_WINDOW_TRADING_DAYS = 90   # w = 90 거래일 관측치
YELLOW_SIGMA = 2.0
RED_SIGMA = 3.0
EPISODE_COOLDOWN_TRADING_DAYS = 10
HORIZON_MONTHS = 6
TAU0 = 1.0 / 365.0              # 거래일 관측치당 (foundation 동일)

# --------------------------------------------------- ingestion
# Shared fetch warm-up buffer.
# Used by daily ingestion and audit reproducibility checks.
# This is an operational data retrieval parameter and does not define
# model structure, calibration constants, or prospective evaluation rules.
FETCH_BUFFER_DAYS = 300

# Planned freeze target date for scheduling and documentation only.
# This value does not define the prospective evaluation anchor.
# The actual anchor is LIVE_FREEZE_DATE, which is set only in the freeze commit.
PROSPECTIVE_TARGET_FREEZE_DATE = "2026-08-03"

# --------------------------------------------------------------- outcome
# SPEC §4 (calibration 이전 확정 — 근거는 SPEC §4.1)
COLLAPSE_DRAWDOWN = 0.25

# ---------------------------------------------------- calibration events
# SPEC §5.1 — window가 "고정 ✓"인 사건은 foundation 공개 값 상속.
# 신규 사건은 calibration/C-US/calibration_plan.md v1 사전등록 후 반영.
# 이 파일은 사전등록 plan의 event_id와 코드 event key를 맞춘다.
CALIBRATION_EVENTS = {
    "GFC_2008": {
        "kind": "positive",
        "stable": ("2004-01-01", "2006-12-31"),      # foundation Supp T18 상속
        "control": ("2004-01-09", "2006-06-30"),     # foundation 상속
        "crisis": ("2005-01-05", "2009-03-31"),      # foundation 상속
        "modes": ["historical_repro", "live"],
    },
    "CREDIT_SHOCK_2020": {
        "kind": "positive",
        "stable": ("2014-01-01", "2018-12-31"),
        "control": ("2017-01-01", "2018-12-31"),
        "crisis": ("2020-01-01", "2020-06-30"),
        "modes": ["live"],
    },
    "SVB_2023": {
        "kind": "positive",
        "stable": ("2021-01-01", "2021-12-31"),
        "control": ("2021-01-01", "2021-12-31"),
        "crisis": ("2023-01-01", "2023-06-30"),
        "modes": ["live"],
    },
    "REPO_2019": {
        "kind": "negative",
        "stable": ("2014-01-01", "2018-12-31"),      # foundation Supp T10 상속
        "control": ("2017-01-01", "2018-12-31"),     # foundation 상속
        "crisis": ("2019-01-01", "2020-02-29"),      # foundation 상속
        "modes": ["historical_repro", "live"],
    },
    "QUIET_2017": {
        "kind": "negative",
        "stable": ("2014-01-01", "2016-12-31"),
        "control": ("2015-01-01", "2016-12-31"),
        "crisis": ("2017-01-01", "2017-12-31"),  # negative control evaluation window
        "modes": ["live"],
    },
}

# --------------------------------------------------- live archive (freeze)
# SPEC §2.1 — calibration 후 숫자 박제. freeze 전까지 None.
# writer는 snapshot_status가 valid/correction일 때 아래 상수와의 일치를 강제한다
# (dry_run은 예외 — freeze 이전 시운전 전용, 평가 제외).
LIVE_STABLE_WINDOW = None          # [TODO] ("YYYY-MM-DD", "YYYY-MM-DD")
LIVE_P99 = None                    # [TODO] {"rho": float, "psi": float, "omega": float}
LIVE_MU_SIGMA = None               # [TODO] {"mu": float, "sigma": float}
LIVE_FREEZE_DATE = None            # [TODO] "YYYY-MM-DD" — freeze commit일 = Π 적분 원점
