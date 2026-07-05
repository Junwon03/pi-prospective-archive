# SPEC-1.0_common — 공통 운영 헌법 (v4)

> 역할: 모든 subtrack이 따르는 **운영 원칙**. 채널·정규화·alert 숫자·outcome은 각 subtrack SPEC에 있음.
> freeze 단위: **이 파일과 각 subtrack SPEC은 독립적으로 freeze된다.** 각 subtrack의 prospective 시계는 *그 subtrack SPEC의 freeze 시점*부터 시작한다.
> 상태: DRAFT v4 — 미동결.
> v1 → v2: **C4.5 Live 인과성 원칙 신설(★)**, C10.2 채널별 fill rule 구조, C10.3 SOURCE_SCHEMA_CHANGE 추가, C12 인과성 검증.
> v2 → v3: C11.3 computed 스키마에 **computed_status** 추가, Π 적분 원점은 subtrack SPEC 정의.
> v3 → v4 (**simplicity pass**): 공격면 축소·재현성 강화. 원칙 — **"SPEC의 모든 약속은 기계 검증되거나 삭제된다."**
> ① alert.json = 일 단위 기록만 (episode는 평가 시 유도 — 상태 저장 제거)
> ② provenance 정본 = raw.csv (meta는 요약 — 이중 기록 제거)
> ③ manifest = run 폴더 내 4파일만 (SPEC·코드·환경 무결성은 meta의 git commit + hash가 담당 — git이 repo 전체를 이미 Merkle tree로 고정하므로 중복 hash 제거)
> ④ snapshot_status에 **dry_run** 신설 (freeze 이전 시운전 전용, 평가 제외)
> ⑤ 공식 snapshot은 frozen 상수(P99/μσ/freeze_date)와의 일치를 코드가 강제
> ⑥ Zenodo 월간 → 분기 (증거력 동일, 운영 부담 감소) / health check 필수 3종 + 권장 4종

---

## C1. Scope

**이것은:** prospective evidence archive.
각 subtrack의 freeze 시점부터 채널 정의·정규화·alert 규칙·outcome 판정 규칙을 고정하고, 매 실행을 변조 불가능하게 기록한다. 목적: "사후에 맞춘 것이 아니라, 이 시점부터 룰을 고정하고 기록했다"의 증명.

**이것이 아닌 것:**
- pi-index.org 대시보드 (별도 repo — C8)
- 예측 서비스 / 투자 신호. **Alerts are research records, not recommendations. Nothing in this archive constitutes investment advice.**
- 가변 분석 환경 (freeze 후 frozen 정의 변경 불가)

## C2. Subtrack 체계와 시계 독립

명명: `SPEC-{ver}-{track}-{region}` (예: SPEC-1.0-C-US, SPEC-1.0-M-KR).

- 각 subtrack은 자신의 SPEC 파일을 갖고, **자기 freeze일 + 자기 시계**로 독립 운영된다.
- 나중에 추가되는 subtrack(예: M-JP)은 추가 시점에 freeze되며 기존 subtrack의 시계를 물려받지 않는다.
- subtrack 간 결과는 섞지 않는다. 각자 독립 평가.
- snapshot 저장도 물리적으로 분리: `snapshots/C-US/…`, `snapshots/M-KR/…`.

## C3. 채널 배치 규칙 (모든 subtrack 공통)

변수는 "고르는" 게 아니라 역할에 **배치**된다 (foundation Methods 4 criteria):
1. **Causal ordering** — ρ는 Ψ·Ω의 시간상 upstream.
2. **Domain independence** — 각 채널은 서로 다른 측정 영역. 단일 자산 내부 피처(같은 자산의 수익률·변동성·거래량) 조합 금지 — 중복 채널은 곱셈 신호를 희석함(falsifiable boundary).
3. **Observability** — 공개·권위 소스.
4. **Non-redundancy** — stable 기간 pairwise `max|r| < 0.7`.

**소스 안정성 규칙:** "현재 살아있음"으로 부족. **1~2년 무인 fetch를 견딜 안정 API**(FRED 급) 우선. 스크래핑 의존 소스는 대체 불가 시에만 + missing-data 정책(C10.2)과 함께 허용. 소스 안정성은 각 subtrack calibration의 통과 항목이다.

## C4. Variable-selection policy

이 아카이브는 **변수선택 알고리즘을 사용하지 않는다.**
근거: 선택 알고리즘(MI 등)은 crisis/control 라벨이 필요하다. prospective에는 미래 라벨이 없으므로, freeze 시점의 알고리즘 선택은 과거 위기에 맞추는 것 — "기계가 한 post-hoc fitting"이다. post-hoc 방어는 **역할 구조(C3) + 사전동결 + 시간순서**로 한다. MI 알고리즘은 후속 논문의 "사람 선택 vs 알고리즘 선택" 비교 검증 도구로만 쓴다(이 아카이브 밖).

## C4.5 Live 인과성 원칙 (★ v2 신설 — 모든 subtrack 강제)

> **Live archive computations must be causal (as-of):** the computed value for snapshot date *t* may use only observations that were visible as of *t*. **No computation may require future observations** — this prohibits, in live snapshots, any alignment or interpolation that needs a later data point (e.g., linear interpolation between weekly observations, centered rolling windows, backward fill).
>
> Permitted live alignment: **latest observation carried forward (LOCF)** within the channel-specific fill limits of the subtrack SPEC.
>
> Historical *reproduction* of published results (e.g., foundation-paper replication) may use the original non-causal procedures, but only in a separately labeled reproduction mode inside `calibration/`, never in live snapshots. **Calibration runs of the live specification must use the full live causal rules end-to-end** — otherwise calibration validates a different computation than the one being frozen.
>
> 검증 가능 조건(= data contract 항목): 데이터를 시점 *t*에서 절단하고 계산한 값과, 전체 데이터로 계산한 뒤 *t* 이전을 본 값이 **완전히 일치**해야 한다 (no-lookahead invariance).

## C5. Calibration의 역할 제한 (모든 subtrack 공통)

> **Calibration is not used to maximize historical performance. Its role is limited to excluding specifications that are unavailable, redundant, structurally missing, or directionally inconsistent with known stress episodes. Passing calibration is a usability check, not evidence of superior performance.**
>
> **Retrospective pre-freeze tests are NOT counted as prospective evidence. Prospective evidence begins only after the subtrack SPEC freeze.**

공통 pass/fail 골격 (숫자·사건 목록은 subtrack SPEC에서 확정):
1. 모든 필수 시리즈 존재 + 계속 업데이트됨
2. stable 기간 `max|r| < 0.7`
3. 사전 고정된 positive 사건에서 `Sep(Π) > 1.0`
4. 동일 사건에서 `Sep(S̄) ≥ 1.0` (window-length 아티팩트 아님)
5. 구조적 결측/단종 없음
6. 소스 안정성 규칙(C3) 통과
+ **negative control**: 사전 고정된 quiet/near-miss 구간에서 red episode가 발생하지 않아야 함.

**사전등록 메커니즘:** calibration 사건 목록·각 사건의 window 날짜·정규화 방식은 **calibration 실행 전에 `calibration/{subtrack}/calibration_plan.md`로 commit**한다. commit timestamp가 "돌리기 전에 고정했다"의 증거가 된다. 실행 후 plan 수정 금지 — 수정 필요 시 새 plan 파일 + 사유 기록.

**전면 공개 원칙:** pass/fail 판정만 기록하지 않는다. 모든 조합·모든 사건의 Sep(Π), Sep(S̄), stable max|r|, red episode 수, 결측률 raw 결과를 `calibration/{subtrack}/`에 전부 저장·공개한다.

## C6. Alert episode 정의 (공통 골격)

alert는 일 단위가 아니라 **episode 단위**로 센다. (연속 red 20일 = false alarm 20개 ✗, episode 1개 ✓)

```
- episode open  : red 기준 첫 충족일
- episode close : S̄_w가 yellow 기준 미만으로 연속 [cooldown]일(거래일) 유지된 날
- horizon       : episode open일 기준으로 계산
- episode_id    : {subtrack}-red-{open일}
- open 중 재상승 : 같은 episode (새 episode ✗)
```
cooldown 일수는 subtrack SPEC에서 숫자로 동결.

**저장 원칙 (v4 simplicity):** episode는 frozen 규칙과 computed 시계열로부터 **결정론적으로 유도**되므로 snapshot에 상태를 저장하지 않는다. 매일의 alert.json은 그날의 레벨만 기록하고, episode 판정은 평가 시점에 computed 시계열 전체로부터 계산한다. (같은 정보를 두 곳에 저장하면 불일치 리스크만 생긴다.)

## C7. Outcome 판정 공통 골격 (confusion matrix)

| 결과 | 정의 |
|---|---|
| hit | red episode open 후 horizon 내 collapse 발생 |
| near-miss | red episode open 후 horizon 내 correction (collapse 미달) |
| false alarm | red episode open 후 horizon 내 correction 미만 |
| miss | collapse 발생 전 horizon 내 red episode 없음 |

보고 지표: precision, recall, lead time, false-positive rate — 모두 **episode 단위**.

**기대치 박제:** 검증 창 내 collapse가 없을 수 있다. 그 경우의 결과("동결 룰이 false alarm을 내지 않음" + near-miss 식별)도 계획된 유효한 prospective 결과다. 사건 발생은 보너스이지 성립 조건이 아니다.

**outcome 시리즈 결정 기준:** ① 공개·살아있음 ② 어떤 입력 채널과도 동일 시리즈 아님(불가피한 중첩은 subtrack SPEC에 명시적 인정 + secondary 병행) ③ 판정이 기계적(재량 없음).
**outcome 소스 요구조건 (입력과 분리):** 입력 채널은 매일 무인 fetch 생존이 필수(point-in-time 기록 자체가 증거이므로). outcome 시리즈는 **평가 시점에 공개적으로 재구성 가능**하면 충분 — 매일 snapshot은 권장이지 freeze 요건 아님.

## C8. 대시보드 분리

pi-index.org와 물리적으로 분리된 별도 repo. 코드·데이터 공유 없음. 대시보드는 이 아카이브를 *읽을* 수 있으나 *쓸* 수 없다.

## C9. Versioning (immutable versioning)

- freeze된 SPEC 파일(common 및 각 subtrack)은 수정하지 않는다.
- 변경 필요 시 새 버전 파일(SPEC-2.0_common, SPEC-2.0-C-US 등)로 분기, 별도 track 시작.
- 버전 간 결과는 절대 섞지 않는다.
- **동결 후 변경 허용범위:** *Implementation improvements are allowed after freeze only if they do not alter frozen definitions, thresholds, transformations, or outcome rules. Any change that affects the interpretation of computed values requires a new SPEC version.* (파이프라인 리팩토링·health check·로깅 = 허용. 채널·변환·threshold·outcome·alert metric에 닿으면 = 새 버전.)

## C10. Operational policies

### C10.1 Timezone / calendar
- 모든 snapshot timestamp는 UTC.
- 시장 관측치는 해당 시장의 local trading date에 귀속.
- 소스가 local close 이후 갱신되면 다음 예정 snapshot이 새로 보인 값을 기록.
- 휴장일 gap은 subtrack SPEC 변환 규칙에 명시된 경우에만 forward-fill.
- subtrack별 캘린더 독립 (C-US 미국 / M-KR 한국). cross-track 정렬 안 함.

### C10.2 Missing data (v2 — 채널별 fill rule 구조)
- 필수 채널 결측 시: raw 층은 결측 그대로 기록 / computed 층은 **해당 채널의 subtrack SPEC fill rule** 미적용 시 S·Π를 unavailable로 마킹 / **raw 층 수동 backfill 절대 금지** / 제공자 정정 데이터는 이후 snapshot에만 반영(과거 snapshot 불변).
- fill rule은 **채널별로** subtrack SPEC에 명시한다 (발표 주기가 다른 채널은 허용 gap도 달라야 함 — 예: 일별 채널 ≤ 5일, 주간 채널 ≤ 14일). 모든 fill은 LOCF만 허용(C4.5 인과성).

### C10.3 Correction / supersession
- 같은 날 재실행은 새 run 폴더로 (과거 수정 ✗, 삭제 ✗). 기존 run의 meta를 고쳐 `superseded`로 바꾸지 않는다. 새 correction run의 `supersedes`가 이전 run_id를 가리킨다.
- meta.json에 `snapshot_status: valid | correction | dry_run`, `supersedes`, `correction_reason`. `correction`은 `correction_reason`과 `supersedes`를 반드시 가진다.
- **dry_run (v4 신설):** freeze 이전 시운전 전용. frozen 상수 강제 없음, **평가에서 항상 제외.** 공식 snapshot(valid/correction)은 frozen 상수(P99·μσ·freeze_date)와의 일치를 writer가 강제한다.
- **correction_reason controlled vocabulary (v2):**
  `FRED_API_OUTAGE / PARTIAL_FETCH_FAILURE / CODE_BUG_NON_SPEC / HASH_VALIDATION_FAILURE / SOURCE_REVISION_VISIBLE_LATER / SOURCE_SCHEMA_CHANGE`
- **평가 코드 의무:** 각 날짜에서 `status ∈ {valid, correction}` 중 최신 run만 사용하고, `supersedes`가 가리키는 이전 run은 보존하되 평가 제외.

### C10.4 Manifest 규칙 (v4 — 무결성 분업)
- **manifest.sha256 = run 폴더 내 로컬 4파일만 검증**: `raw.csv, computed.csv, alert.json, meta.json`. manifest는 정확히 이 네 파일만 포함해야 하며, 누락·추가·중복·경로 포함 항목은 검증 실패다. manifest에 적힌 모든 파일은 존재해야 하며 hash가 일치해야 한다.
- **SPEC·코드·환경의 무결성은 meta.json이 담당**: `code_git_commit`(git commit이 repo 전체 — SPEC·코드·과거 snapshot — 를 Merkle tree로 고정), `spec_*_sha256`, `environment_hash`(requirements.lock).
- 근거: git이 이미 보장하는 것을 manifest에 중복 기록하면 검증 표면과 불일치 리스크만 늘어난다. 분업이 단순하고 강하다.

## C11. Snapshot schema

### C11.1 디렉토리
```
snapshots/
  {subtrack}/
    2026-08-15/
      2026-08-15T000500Z/
        raw.csv / computed.csv / alert.json / meta.json / manifest.sha256
      2026-08-15T031200Z_correction/   ← 재실행 시에만
```

### C11.2 raw.csv — long format
```
snapshot_id,subtrack,provider,series_id,observation_date,realtime_start,realtime_end,value,unit,fetch_status,fetched_at_utc
```

### C11.3 computed.csv
```
snapshot_id,subtrack,date,rho_raw,psi_raw,omega_raw,rho_hat,psi_hat,omega_hat,S,Sbar_w,Pi,alert_level,computed_status
```
- **결측 행 삭제 금지:** fill 한도 초과로 계산 불가한 날짜는 행을 지우지 않고 `computed_status = unavailable_fill_limit`로 보존한다. "그 날짜가 없음"과 "그 날짜가 계산 불가였음"은 감사자에게 다른 정보다.
- **Π 적분 원점:** cumsum은 입력 시작점에 의존하므로, live Π의 적분 원점은 각 subtrack SPEC에서 정의·동결한다 (예: C-US = Pi_since_freeze).

### C11.4 alert.json — 일 단위 (v4 simplicity)
```json
{
  "snapshot_id": "…", "subtrack": "…", "alert_metric": "Sbar_w",
  "asof_date": "…", "alert_level": "none | yellow | red"
}
```
episode 필드는 저장하지 않는다 — C6 저장 원칙 참조 (평가 시 computed로부터 유도).

### C11.5 meta.json (v4)
```json
{
  "snapshot_id": "…", "subtrack": "…", "spec_version": "SPEC-1.0",
  "created_at_utc": "…", "code_git_commit": "…",
  "p99_used": {"rho": 0, "psi": 0, "omega": 0},
  "mu_sigma_used": {"mu": 0, "sigma": 0},
  "freeze_date": "…",
  "spec_common_sha256": "…", "spec_subtrack_sha256": "…",
  "environment_hash": "…",
  "snapshot_status": "valid | correction | dry_run",
  "supersedes": null, "correction_reason": null,
  "data_sources": ["DFF", "DCPF3M", "DTB3", "TOTBKCR"],
  "raw_sha256": "…", "computed_sha256": "…", "alert_sha256": "…"
}
```
- **provenance 정본 = raw.csv** — 각 행이 realtime_start/end·observation_date·fetched_at_utc를 보유한다. `data_sources`는 시리즈 목록 **요약**일 뿐이며 provenance를 중복 기록하지 않는다.
- `p99_used`·`mu_sigma_used`·`freeze_date`: 이 snapshot의 computed가 정확히 어떤 상수로 계산됐는지 박제 — raw + 이 상수만으로 computed가 완전 재생성된다.

## C12. Data contract (v2 — 인과성 검증 포함)

schema 검증 실패 = snapshot 생성 실패 (불완전 snapshot이 valid처럼 보이면 안 됨).
- raw: 필수 컬럼 존재 / value 숫자 또는 명시적 missing / observation_date 미래면 실패 / provider·series_id 공백이면 실패
- computed: 필수 컬럼 존재 / **S = ρ̂·Ψ̂·Ω̂ 재계산 일치** / 공식 snapshot(valid/correction)의 computed_status=ok 행 alert_level ∈ {none,yellow,red}; dry_run에서 μ/σ 미확정이면 ok 행 alert_level=null 허용 / unavailable 행은 null
- **공식 snapshot(valid/correction)의 frozen 상수 일치**: p99_used = LIVE_P99, mu_sigma_used = LIVE_MU_SIGMA, freeze_date = LIVE_FREEZE_DATE — writer가 강제, 불일치 시 snapshot 생성 실패. dry_run은 예외(평가 제외 신분)
- **인과성(no-lookahead) 검증:** 임의 시점 t에서 데이터를 절단해 재계산한 값이 전체 데이터 계산의 t 이전 값과 일치 (C4.5) — CI 테스트로 상시 검증
- meta: code_git_commit·spec hash·파일 hash 존재
- manifest: 전체 hash 검증 통과

## C13. Pipeline 원칙 (idempotent + atomic)

```
새 run_id 생성 → 임시폴더 fetch → raw 저장 → computed 생성 → schema+인과성 검증
→ hash 생성 → manifest 생성 → 최종 snapshot 폴더로 atomic move → git commit → push
```
- 같은 run_id 재실행 시 기존 파일 덮어쓰기 금지.
- 중간 실패 시 snapshot 폴더 미생성 또는 `failed_runs/`에 격리.

## C14. Repo 운영

- main branch protection ON: **force-push 금지 / branch deletion 금지**. 이 둘이 append-only 증거력의 핵심이다.
- 운영 모델은 **snapshot bot direct-push**이다. 따라서 main 전체에 required status checks 또는 PR 강제를 걸어 bot push가 막히는 설정은 freeze 전 기본 운영에서 사용하지 않는다. 대신 collect workflow 내부에서 snapshot 생성 전 `pytest`를 실행해 해당 run의 불변량 통과 로그를 남긴다.
- 사람이 하는 코드·SPEC 변경은 PR + CI 통과를 권장한다. signed commits 가능하면 ON. manual direct commit은 최소화한다.
- workflow는 `requirements.lock`을 설치하고, snapshot meta의 `environment_hash`도 같은 `requirements.lock`을 hash한다. 실행 환경과 박제 환경이 달라지면 안 된다.
- `workflow_dispatch`는 main에서만 실행되도록 guard한다. scheduled run은 GitHub Actions 기본 동작상 default branch 기준이지만, 수동 실행 실수를 막기 위해 같은 guard를 둔다.
- **분기 1회** release tag (`q3-2026`) → Zenodo tarball → 불변 DOI (v4: 월간→분기 — GitHub commit이 일 단위 연속성을 이미 제공하므로 증거력 손실 없음, 운영 부담만 감소. Zenodo = out-of-repo 불변 citation)

## C15. Health check (freeze 후 보강 허용, 초기 투입 권장)

**필수 3종 (freeze 전 배선):** ① 최근 snapshot 존재 (N일 이내) ② 필수 series fetch 성공 ③ manifest hash 검증 통과.
**초기 상태 규칙:** `ARCHIVE_STARTED` marker가 repo에 없을 때만 `no_snapshots_yet` 통과를 허용한다. 첫 성공 수집 후 marker가 commit되면 snapshot 부재는 실패다.
**권장 4종 (freeze 후 보강 가능):** raw row count / computed 생성 / alert 생성 / 비정상 NaN 증가.
→ 실패 시 알림. 무인화의 전제 = "깨지면 알아챈다". (v4: 필수/권장 분리 — 약속을 지킬 수 있는 크기로.)

## C16. README = audit guide

README는 소개문이 아니라 감사 안내서:
1. What this archive is / is not
2. How prospective evidence starts (subtrack freeze dates)
3. Subtracks and clocks
4. **How to verify a snapshot** (한 명령어로 manifest/hash/schema/S 재계산/인과성 검증)
5. How to reproduce computed from raw
6. How corrections are handled
7. Not for investment use
8. Citation and quarterly DOI releases
