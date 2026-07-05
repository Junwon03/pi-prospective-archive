"""Snapshot writer — common C11(schema)·C12(contract)·C13(atomic pipeline) 구현.

핵심 보장:
- point-in-time: 오늘 fetch한 raw로 오늘 computed를 만들고 함께 박제.
  과거 snapshot은 절대 재계산·수정하지 않는다 (common C4.5, C10.2).
- append-only: 동일 run 디렉토리가 존재하면 거부 (덮어쓰기 금지).
- atomic: 임시 디렉토리에 전부 생성·검증 후 최종 경로로 한 번에 이동.
- 감사 가능성: 결측 행을 삭제하지 않고 computed_status로 기록.
- Π 정의: live Π = Pi_since_freeze (적분 원점 = freeze일; SPEC C-US §3).

Simplicity pass 원칙 (common v4):
- alert.json = 일 단위 기록만. episode는 frozen 규칙에서 결정론적으로 유도되므로
  평가 시점에 computed 시계열로부터 계산 — snapshot에 상태 저장 안 함.
- provenance 정본 = raw.csv (각 행이 realtime_start/end·fetched_at 보유).
  meta.data_sources는 요약(시리즈 목록)일 뿐.
- 무결성 분업: manifest = run 폴더 내 4파일 검증 / SPEC·코드·환경 = meta의
  git commit + spec/lock hash (git이 repo 전체를 이미 Merkle tree로 고정).
- dry_run 분리: freeze 이전(mu_sigma/frozen 상수 미확정) snapshot은 반드시
  snapshot_status="dry_run" — 평가에서 제외되는 별도 신분.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from . import channels as ch
from . import config, stress

RAW_COLUMNS = ["snapshot_id", "subtrack", "provider", "series_id",
               "observation_date", "realtime_start", "realtime_end",
               "value", "unit", "fetch_status", "fetched_at_utc"]

COMPUTED_COLUMNS = ["snapshot_id", "subtrack", "date",
                    "rho_raw", "psi_raw", "omega_raw",
                    "rho_hat", "psi_hat", "omega_hat",
                    "S", "Sbar_w", "Pi", "alert_level", "computed_status"]

MANIFEST_FILES = {"raw.csv", "computed.csv", "alert.json", "meta.json"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_raw_contract(raw_out: pd.DataFrame, now: dt.datetime) -> None:
    """common C11.2/C12 raw contract의 최소 기계 검증."""
    if raw_out.empty:
        raise ValueError("raw schema violation: raw.csv would be empty")
    missing_cols = [c for c in RAW_COLUMNS if c not in raw_out.columns]
    if missing_cols:
        raise ValueError(f"raw schema violation, missing: {missing_cols}")

    for col in ("provider", "series_id"):
        blank = raw_out[col].isna() | (raw_out[col].astype(str).str.strip() == "")
        if bool(blank.any()):
            raise ValueError(f"raw schema violation: blank {col}")

    obs_dates = pd.to_datetime(raw_out["observation_date"], errors="coerce")
    if bool(obs_dates.isna().any()):
        raise ValueError("raw schema violation: invalid observation_date")
    now_date = pd.Timestamp(now.date())
    if bool((obs_dates.dt.normalize() > now_date).any()):
        raise ValueError("raw schema violation: observation_date is in the future")

    non_missing = raw_out["value"].notna()
    numeric = pd.to_numeric(raw_out.loc[non_missing, "value"], errors="coerce")
    if bool(numeric.isna().any()):
        raise ValueError("raw schema violation: value must be numeric or explicit missing")


# ---------------------------------------------------------- computed 조립

def build_live_computed(raw: dict[str, pd.Series], p99: dict, mu_sigma: dict | None,
                        freeze_date: str, snapshot_id: str, subtrack: str
                        ) -> pd.DataFrame:
    """live rule 전 구간 적용 computed. 결측 행 보존 + status 기록.

    mu_sigma=None(pre-freeze dry-run)이면 alert_level은 null로 둔다.
    """
    chan_full = ch.build_credit_channels(raw, mode="live", drop_incomplete=False)
    valid_mask = chan_full.notna().all(axis=1)
    valid = chan_full[valid_mask]

    st = stress.compute_stress(stress.normalize(valid, p99))
    st["Pi"] = stress.pi_since(st["S"], freeze_date)

    out = pd.DataFrame(index=chan_full.index)
    out[["rho_raw", "psi_raw", "omega_raw"]] = chan_full
    for col in ("rho_hat", "psi_hat", "omega_hat", "S", "Sbar_w", "Pi"):
        out[col] = st[col]  # invalid 행은 자동 NaN
    out["computed_status"] = ["ok" if v else "unavailable_fill_limit"
                              for v in valid_mask]

    if mu_sigma is None:  # dry_run 전용: threshold 미확정이면 alert를 저장하지 않는다.
        # dry_run 신분은 meta.snapshot_status가 담당한다. alert_level에
        # pending_freeze 같은 제4상태를 넣으면 common C11.4의 단순 스키마와 충돌한다.
        out["alert_level"] = None
    else:
        mu, sd = mu_sigma["mu"], mu_sigma["sigma"]
        red_thr, yel_thr = mu + config.RED_SIGMA * sd, mu + config.YELLOW_SIGMA * sd

        def level(x):
            if pd.isna(x):
                return None
            if x > red_thr:
                return "red"
            if x > yel_thr:
                return "yellow"
            return "none"

        out["alert_level"] = out["Sbar_w"].map(level)

    out.insert(0, "date", out.index.strftime("%Y-%m-%d"))
    out.insert(0, "subtrack", subtrack)
    out.insert(0, "snapshot_id", snapshot_id)
    return out.reset_index(drop=True)


# ------------------------------------------------------------ 메인 writer

def write_snapshot(raw_long: pd.DataFrame,
                   raw_series: dict[str, pd.Series],
                   subtrack: str,
                   base_dir: str | Path,
                   spec_paths: dict[str, str | Path],
                   p99: dict,
                   freeze_date: str,
                   mu_sigma: dict | None = None,
                   lock_path: str | Path | None = None,
                   code_git_commit: str | None = None,
                   snapshot_status: str = "valid",
                   supersedes: str | None = None,
                   correction_reason: str | None = None,
                   now_utc: dt.datetime | None = None) -> Path:
    """하나의 snapshot을 생성해 base_dir/{subtrack}/{date}/{run_id}/에 박제.

    common C13 순서: 임시폴더 생성 → raw/computed/alert/meta 작성 → 검증
    → manifest 작성 → 최종 경로로 atomic move. 실패 시 최종 폴더 미생성.
    반환: 최종 run 디렉토리 경로.
    """
    allowed_status = {"valid", "correction", "dry_run"}
    if snapshot_status not in allowed_status:
        raise ValueError(f"snapshot_status must be one of {allowed_status}")

    # correction은 사유가 있어야 하고, correction이 아닌 run은 사유를 달 수 없다.
    # controlled vocabulary 밖의 사유는 감사 표면을 넓히므로 거부한다.
    vocab = {"FRED_API_OUTAGE", "PARTIAL_FETCH_FAILURE", "CODE_BUG_NON_SPEC",
             "HASH_VALIDATION_FAILURE", "SOURCE_REVISION_VISIBLE_LATER",
             "SOURCE_SCHEMA_CHANGE"}  # common C10.3 controlled vocabulary
    if correction_reason is not None and correction_reason not in vocab:
        raise ValueError(f"correction_reason not in controlled vocabulary: "
                         f"{correction_reason}")
    if snapshot_status == "correction" and correction_reason is None:
        raise ValueError("correction snapshots require correction_reason")
    if snapshot_status == "correction" and not supersedes:
        raise ValueError("correction snapshots require supersedes")
    if snapshot_status != "correction" and correction_reason is not None:
        raise ValueError("correction_reason is only allowed for correction snapshots")
    if snapshot_status != "correction" and supersedes is not None:
        raise ValueError("supersedes is only allowed for correction snapshots")

    if snapshot_status == "dry_run":
        pass  # freeze 이전 시운전 — frozen 상수 강제 없음, 평가 제외
    else:
        # valid/correction = 공식 snapshot: frozen 상수와 일치해야 함 (common C12)
        if mu_sigma is None:
            raise ValueError(
                "mu_sigma is required for official snapshots; "
                "pre-freeze runs must use snapshot_status='dry_run'")
        for name, given, frozen in (
            ("p99", p99, config.LIVE_P99),
            ("mu_sigma", mu_sigma, config.LIVE_MU_SIGMA),
            ("freeze_date", freeze_date, config.LIVE_FREEZE_DATE),
        ):
            if frozen is None:
                raise ValueError(
                    f"config.LIVE_{name.upper()} is not frozen yet; "
                    "official snapshots are forbidden before freeze")
            if given != frozen:
                raise ValueError(
                    f"data contract violation: {name} does not match frozen "
                    f"config (given={given}, frozen={frozen})")
        # 공식 snapshot은 제3자가 repo 상태와 환경을 추적할 수 있어야 한다.
        if not code_git_commit:
            raise ValueError("code_git_commit is required for official snapshots")
        if lock_path is None or not Path(lock_path).is_file():
            raise ValueError("requirements.lock path is required for official snapshots")
        required_specs = {"common", "subtrack"}
        if set(spec_paths) != required_specs:
            raise ValueError("spec_paths must contain exactly 'common' and 'subtrack' for official snapshots")
        for name, spec_path in spec_paths.items():
            if not Path(spec_path).is_file():
                raise ValueError(f"spec path missing for {name}: {spec_path}")

    now = now_utc or dt.datetime.now(dt.timezone.utc)
    snapshot_id = now.strftime("%Y-%m-%dT%H%M%SZ")
    date_str = now.strftime("%Y-%m-%d")

    base = Path(base_dir)
    suffix = "" if snapshot_status == "valid" else f"_{snapshot_status}"
    final_dir = base / subtrack / date_str / f"{snapshot_id}{suffix}"
    if final_dir.exists():
        raise FileExistsError(f"append-only violation: {final_dir} already exists")

    # ---- 임시 폴더에서 전부 생성 (atomic 보장) ----
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=final_dir.parent, prefix=".tmp_"))
    try:
        # raw.csv — long format + snapshot_id/subtrack (common C11.2)
        raw_out = raw_long.copy()
        raw_out.insert(0, "subtrack", subtrack)
        raw_out.insert(0, "snapshot_id", snapshot_id)
        _validate_raw_contract(raw_out, now)
        raw_out = raw_out[RAW_COLUMNS]
        raw_path = tmp / "raw.csv"
        raw_out.to_csv(raw_path, index=False)

        # computed.csv
        computed = build_live_computed(raw_series, p99, mu_sigma,
                                       freeze_date, snapshot_id, subtrack)
        computed_path = tmp / "computed.csv"
        computed[COMPUTED_COLUMNS].to_csv(computed_path, index=False)

        # 재계산 일치 검증 (common C12: S = ρ̂·Ψ̂·Ω̂)
        okrows = computed[computed["computed_status"] == "ok"]
        recomputed = okrows["rho_hat"] * okrows["psi_hat"] * okrows["omega_hat"]
        if not ((okrows["S"] - recomputed).abs() < 1e-12).all():
            raise ValueError("data contract violation: S != rho_hat*psi_hat*omega_hat")

        # alert_level contract: 공식 snapshot의 ok 행은 3상태만 허용.
        # unavailable 행은 null이어야 한다. dry_run에서 threshold가 없으면 ok 행도 null 허용.
        unavail = computed[computed["computed_status"] != "ok"]
        if unavail["alert_level"].notna().any():
            raise ValueError("data contract violation: unavailable rows must have null alert_level")
        if snapshot_status != "dry_run":
            allowed_alerts = {"none", "yellow", "red"}
            # rolling warm-up 구간은 Sbar_w가 아직 없으므로 alert_level null 허용.
            evaluable = okrows[okrows["Sbar_w"].notna()]
            vals = set(evaluable["alert_level"].dropna().tolist())
            if evaluable["alert_level"].isna().any() or not vals <= allowed_alerts:
                raise ValueError("data contract violation: official alert_level must be none/yellow/red when Sbar_w is available")

        # alert.json — 최신 유효 관측 기준 (episode 판정은 평가 레이어)
        last_ok = okrows.iloc[-1] if len(okrows) else None
        alert = {
            "snapshot_id": snapshot_id, "subtrack": subtrack,
            "alert_metric": "Sbar_w",
            "asof_date": None if last_ok is None else last_ok["date"],
            "alert_level": None if last_ok is None else last_ok["alert_level"],
        }
        alert_path = tmp / "alert.json"
        alert_path.write_text(json.dumps(alert, indent=2), encoding="utf-8")

        # spec / lock hashes
        spec_hashes = {name: sha256_file(Path(p)) for name, p in spec_paths.items()}
        env_hash = sha256_file(Path(lock_path)) if lock_path else None

        # meta.json (common C11.5)
        meta = {
            "snapshot_id": snapshot_id, "subtrack": subtrack,
            "spec_version": "SPEC-1.0",
            "created_at_utc": now.isoformat(),
            "code_git_commit": code_git_commit,
            "p99_used": p99, "mu_sigma_used": mu_sigma,
            "freeze_date": freeze_date,
            **{f"spec_{k}_sha256": v for k, v in spec_hashes.items()},
            "environment_hash": env_hash,
            "snapshot_status": snapshot_status,
            "supersedes": supersedes,
            "correction_reason": correction_reason,
            "data_sources": sorted(raw_long["series_id"].unique().tolist()),
            "raw_sha256": sha256_file(raw_path),
            "computed_sha256": sha256_file(computed_path),
            "alert_sha256": sha256_file(alert_path),
        }
        meta_path = tmp / "meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        # manifest.sha256 (common v4 C10.4 — run 폴더 내 로컬 파일만.
        # SPEC·코드·환경 무결성은 meta의 git commit + spec/lock hash가 담당:
        # git commit이 repo 전체를 Merkle tree로 고정하므로 중복 hash 불필요)
        lines = [f"{sha256_file(p)}  {p.name}"
                 for p in (raw_path, computed_path, alert_path, meta_path)]
        (tmp / "manifest.sha256").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")

        os.replace(tmp, final_dir)  # atomic move
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return final_dir


def verify_snapshot(run_dir: str | Path) -> bool:
    """manifest의 파일 hash 재검증 (README 'How to verify a snapshot').

    common v4 simplicity contract: manifest는 정확히 네 로컬 파일
    raw.csv/computed.csv/alert.json/meta.json만 포함해야 한다. 누락·추가·중복·
    경로 포함 항목은 모두 실패다.
    """
    run_dir = Path(run_dir)
    try:
        manifest = (run_dir / "manifest.sha256").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False

    seen: list[str] = []
    for line in manifest.strip().splitlines():
        try:
            digest, name = line.split(None, 1)
        except ValueError:
            return False
        name = name.strip()
        if name in seen or name not in MANIFEST_FILES:
            return False
        if "/" in name or "\\" in name:
            return False
        f = run_dir / name
        if not f.exists():
            return False
        if sha256_file(f) != digest:
            return False
        seen.append(name)
    return set(seen) == MANIFEST_FILES
