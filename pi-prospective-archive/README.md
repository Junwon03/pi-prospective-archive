# pi-prospective-archive — C-US calibration & core (SPEC-1.0)

SPEC-1.0-C-US v5의 기계적 구현. **SPEC 문서가 헌법, 이 코드는 그 표현** —
`src/pi_archive/config.py`의 상수는 SPEC frozen 정의와 1:1 대응한다.

## 구조
```
src/pi_archive/
  config.py       SPEC frozen 상수 (채널·fill·alert·outcome·calibration 사건)
  channels.py     인과적(as-of) 정렬·변환 — look-ahead 원천 차단 (common C4.5)
  stress.py       P99 정규화, S/S̄_w/Π, episode 로직 (common C6)
  calibration.py  사건 실행기 — raw 지표 전량 산출 + strict mode (common C5)
  writer.py       snapshot writer — raw/computed/alert/meta/manifest, atomic, append-only (C11~C13)
  fetch_fred.py   FRED fetch (long format + vintage 메타)
tests/test_core.py  핵심 불변량 (아래)
run_calibration.py  CLI: fetch → run
```

## 상태 (정확한 표현)
**core 계산 + snapshot writer + 일일 수집/health check: 단위테스트 39/39 통과.** 단, prospective archive 운영 파이프라인
중 **snapshot writer·manifest·meta·atomic move·append-only는 구현·테스트 완료.** workflow(CI·일일 수집·health check)까지 동봉 — 남은 것: repo 셋업(아래 절차) + branch protection + Zenodo 연동 + 7일 dry-run.

## 검증된 불변량 (39/39 통과)
- **no-lookahead**: t 절단 계산 == 전체 계산의 t 이전 값 (channels + S/S̄/Π 전 구간, exact)
- **보간 비인과성 실증**: 선형보간은 주간 관측 사이 값에 미래 관측이 개입 → live 금지 근거
- fill rule: 주간 LOCF ≤14d 정상 / 일별 5d 초과 gap → computed 탈락(unavailable)
- S = ρ̂·Ψ̂·Ω̂ 재계산 일치 / stable 구간 x̂ P99 ≈ 1 / Sep(Π)·Sep(S̄) 알려진 비율 재현
- episode: 짧은 dip은 1 episode / cooldown 10거래일 경과 후 재상승은 2 episode / yellow만으로 미개시
- **사전등록 강제**: window 미등록 사건 실행 시 RuntimeError
- **writer**: 5파일 생성 + manifest hash 검증, computed_status로 결측 기록(행 삭제 없음), append-only 위반 거부, correction 통제 어휘 강제
- **verify 버그픽스**: manifest에 적힌 파일이 누락되면 검증 실패 (이전엔 건너뛰고 True — 수정·테스트됨)
- **manifest 최소주의**: run 폴더 4파일만 커버함을 테스트로 고정 (SPEC/lock은 meta 담당)
- **dry_run 강제**: freeze 전 status=valid 거부 / frozen 상수 미설정 시 공식 snapshot 거부 / 상수 불일치 거부·일치 통과
- **official metadata 강제**: valid/correction은 code_git_commit·requirements.lock·SPEC hash를 반드시 보유
- **workflow 정합성**: collect workflow는 snapshot 쓰기 전에 pytest를 직접 실행하고, 실제 checkout HEAD를 meta.code_git_commit에 기록
- **health marker**: `ARCHIVE_STARTED` 이후에는 snapshot 부재가 healthcheck green으로 숨지 않음
- **dry_run alert 단순화**: threshold 미확정이면 alert_level은 null, 신분은 meta.snapshot_status로만 표현
- **Pi_since_freeze**: fetch 시작점이 달라도 freeze 이후 Π 값 동일 (적분 원점 고정)
- **strict mode**: TODO window 존재 시 freeze-prep run 실패
- **SPEC-코드 일치**: repro 모드 Ψ = |Δ5|TEDRATE 정확 재현 / TEDRATE 없이 repro 호출 거부 / DGS3MO sensitivity가 결과에 기록되되 pass/fail 판정에 영향 0 (값을 바꿔도 판정 불변)

## 실행 (로컬)
```
export FRED_API_KEY=...
python run_calibration.py fetch   # 1997~ 전 시리즈 (TEDRATE 과거값 포함)
python run_calibration.py run            # 등록 사건 실행 → calibration/C-US/{live,reproduction}/
python run_calibration.py run --strict   # freeze-prep: TODO window 있으면 실패
python -m pytest -q               # 불변량 검증
```

## 남은 절차 (SPEC v5 체크리스트)
1. `calibration/C-US/calibration_plan.md` 작성 — COVID·SVB·quiet window 확정 → **실행 전 commit**
2. plan 값을 `config.py` CALIBRATION_EVENTS에 반영 → `run`
3. 결과 검토 → live stable window 확정 → live P99/μ/σ 산출·박제 (`LIVE_*` 상수)
4. 은행주 지수 소스·FDIC $X 확정
5. GitHub Actions·branch protection·health check 배선 → dry-run 7일 → freeze

## 주의
- historical_repro 모드(NONCAUSAL 보간)는 foundation 재현 전용 — live 경로 사용 금지가
  함수명과 테스트로 강제됨.
- **snapshot 신분 규칙 (v5)**: freeze 이전의 모든 snapshot은 `snapshot_status="dry_run"`
  (평가 제외). 공식 snapshot(valid/correction)은 config의 LIVE_P99/LIVE_MU_SIGMA/
  LIVE_FREEZE_DATE와의 일치를 writer가 강제 — 상수 불일치 시 생성 자체가 실패한다.
- **무결성 분업 (simplicity pass)**: manifest = run 폴더 4파일 / SPEC·코드·환경 = meta의
  git commit + hash. episode는 저장하지 않고 평가 시 computed로부터 유도.

## requirements.lock 주의
workflow는 `requirements.lock`을 설치하고, meta의 `environment_hash`도 같은 파일을 가리킨다.
즉 실행 환경과 박제 환경이 같은 파일에 의해 정의된다. 동봉 lock은 이 패치 검증 환경의
최소 exact pins이며, **freeze 전에는 GitHub runner의 깨끗한 환경에서 설치 후
`pip freeze > requirements.lock`으로 전체 lock을 재생성하고 commit**할 것. lock 설치가 실패하면
조용히 `requirements.txt`로 fallback하지 말고 workflow를 실패시키는 것이 맞다.

## GitHub 셋업 절차 (workflow 가동)

동봉 workflow 3개: `ci.yml`(push마다 39종 테스트), `collect_c_us.yml`(평일 21:30 UTC
일일 snapshot — freeze 전 dry_run / 후 valid 자동 전환), `healthcheck.yml`(23:00 UTC 필수 3종).

1. **새 repo 생성** (public 권장 — 제3자 감사 가능성이 곧 증거력) → 이 폴더 전체 push
2. **Settings → Secrets and variables → Actions** → `FRED_API_KEY` 등록
   (키 발급: https://fred.stlouisfed.org/docs/api/api_key.html)
3. **Settings → Actions → General → Workflow permissions** → "Read and write" 선택
   (봇이 snapshot을 commit·push해야 함)
4. **Branch protection (main)**: force push 차단 + branch deletion 차단.
   ⚠️ snapshot bot direct-push 모델에서는 main 전체에 "Require a pull request"나
   required status checks를 강제하지 말 것 — 봇 push가 막힐 수 있음.
   대신 collect workflow 내부가 `pytest`를 먼저 실행한 뒤 snapshot을 만든다.
   사람이 하는 코드·SPEC 변경은 PR + CI 통과를 권장.
5. **Zenodo 연동** (freeze 시점에): zenodo.org → GitHub 연동 → 이 repo 토글 ON
   → 이후 release(분기 태그)마다 자동 archive + DOI
6. 수동 시운전: Actions 탭 → collect-c-us → "Run workflow". main branch guard가 있으므로
   main에서만 실행된다. 첫 성공 run은 `snapshots/ARCHIVE_STARTED` marker와 `snapshots/`를 함께 commit한다.
7. **7일 dry-run**: 그대로 일주일 방치 → 매일 dry_run이 쌓이고 healthcheck가
   녹색이면 운영 준비 끝. `ARCHIVE_STARTED` 이후에는 snapshot 부재가 healthcheck 실패로 처리된다.
   freeze(config LIVE_* 박제 + SPEC hash 고정) 후부터 snapshot이 자동으로 valid 신분으로 전환됨

## Freeze 전/후 동작 차이 (자동)
- **freeze 전**: config LIVE_* = None → 모든 snapshot이 `dry_run` (평가 제외,
  임시 P99 사용·meta에 박제). 공식 신분으로는 생성 자체가 코드에서 거부됨.
- **freeze 후**: LIVE_P99/LIVE_MU_SIGMA/LIVE_FREEZE_DATE 박제 → `valid` 자동 전환,
  writer가 frozen 상수와의 일치를 매 snapshot 강제.

## Fetch 창 정책 (repo 비대 방지)
매일 1997년부터 전체 fetch ✗ — Pi_since_freeze는 freeze 이후 S만 필요하고
warm-up(90거래일 S̄_w + Δ5 + LOCF)은 300일 버퍼로 커버되므로,
observation_start = (freeze일 또는 오늘) − 300일. snapshot당 raw ~수백 KB로 유계.
