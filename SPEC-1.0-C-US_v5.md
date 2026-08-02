# SPEC-1.0-C-US — 신용 섹터 (미국) subtrack 헌법 (frozen v5)

> 따르는 공통 헌법: **SPEC-1.0_common (v4)** — 해당 hash는 각 snapshot의 meta.json에 박제 (manifest는 run 폴더 로컬 파일만, common v4 C10.4)
> 상태: **FROZEN v5 (documentation closure).** Analytical rule freeze date: **2026-08-03**; analytical freeze commit: `68731c6546ebd4845531aac03e1f3be198aab61a`; release tag: `c-us-freeze-v1.0`. This document reconciles the pre-freeze TODO fields to values already fixed at the analytical freeze, before the first `valid` snapshot. No analytical rule is changed by this documentation closure.
> v2 → v3 (치명 결함 2건 수정 + 정밀화):
> ① **Ω(TOTBKCR) live 정렬을 선형보간 → as-of LOCF로 교체** (선형보간은 미래 관측 필요 = look-ahead. common C4.5 위반이었음)
> ② **정규화 P99 이원화** — calibration용 event-specific P99 vs live frozen P99 명확 분리
> ③ 채널별 fill rule 분리 (일별 채널 ≤5일 / 주간 Ω ≤14일 — 단일 5일 규칙은 주간 시리즈와 양립 불가했음)
> ④ w = 90을 "90 거래일 관측치"로 정밀 정의 (calendar/거래일 모호성 제거)
> ⑤ calibration window 사전등록 메커니즘 (common C5) 반영 — 2008·repo는 foundation 공개 window 상속으로 즉시 고정
>
> v3 → v4: **live Π 정의 = Pi_since_freeze** (적분 원점 = freeze일), computed_status 기록 원칙.
> v4 → v5 (**정합화 + simplicity pass 수용**): 버전 참조 정정(common v4·frozen v5), alert.json 일 단위 기록(episode는 평가 시 유도), 공식 snapshot의 frozen 상수 강제, dry_run 신분 도입, Zenodo 분기 주기 — 모두 common v4 준수. freeze 시 이 파일과 common v4의 hash가 함께 박제된다.
> 정체성: 2008 은행·신용 위기 타입 — foundation 최강 검증 세팅(18.6×)의 prospective 후예.

---

## 1. Frozen channels

| 채널 | 역할 | 정의 | 변환 (live) | 소스 | 상태 |
|---|---|---|---|---|---|
| ρ | 외부압력 (정책금리) | `DFF` | \|Δ over 5 거래일 관측치\| | FRED | 확정 ✓ |
| Ψ | funding stress | **`DCPF3M − DTB3`** (파이프라인 직접 계산) | \|Δ over 5 거래일 관측치\| | FRED × 2 | 확정 ✓ |
| Ω | 은행 신용 | `TOTBKCR` | **level, as-of LOCF 정렬 (§1.4)** | FRED | 확정 ✓ (v3 수정) |

### 1.1 Ψ 정의 및 배제 근거 (박제)

> For the live Ψ channel, we replace the discontinued TEDRATE with a CP–T-bill funding-stress spread defined as **DCPF3M − DTB3**. DCPF3M measures 90-day AA financial commercial paper rates; DTB3 measures the 3-month Treasury bill secondary market rate. This preserves the intended structure of a short-term private financial funding rate relative to a Treasury benchmark — the functional successor of the TED spread (unsecured funding rate minus risk-free rate).
>
> **We do not use CPFF** because it subtracts the effective federal funds rate, which is already used in the ρ channel, creating construction-level dependence between ρ and Ψ.
>
> **We do not use SOFR-based spreads** as the primary replacement because SOFR reflects secured overnight financing, whereas the Ψ channel is intended to capture unsecured short-term financial funding stress.
>
> **Sensitivity (기록 전용):** DCPF3M − DGS3MO is recorded during calibration to assess whether the Treasury-rate basis materially affects the signal. **This sensitivity is not used to change the frozen primary specification after freeze.**

### 1.2 historical / live 조합 분리
- **historical(재현 전용):** `DFF × TEDRATE × TOTBKCR` — foundation 결과 재현. **foundation의 원 절차(선형보간 포함)를 그대로 사용**하되, `calibration/C-US/reproduction/`에 별도 라벨로 격리. live 사용 ✗.
- **live(freeze 대상):** `DFF × (DCPF3M − DTB3) × TOTBKCR` — **live causal rule(§1.4) 전 구간 적용.**
- CP–T-bill spread는 1997년부터 일별 존재 → **2008을 live 조합·live rule로 직접 calibration 가능** (§5.1).

### 1.3 채널별 Fill rule (v3 — 채널별 분리)

> The raw layer always records missing values as observed. In the computed layer, only LOCF (last observation carried forward) is permitted (common C4.5 — no future observations). Channel-specific limits:
>
> | 채널 | 발표 주기 | LOCF 허용 한도 |
> |---|---|---|
> | DFF, DCPF3M, DTB3 | 일별 (영업일) | **≤ 5 calendar days** (공시 gap·휴장 흡수) |
> | TOTBKCR | 주간 | **≤ 14 calendar days** (주간 주기 7일 + 발표 지연 여유) |
>
> If any required channel remains missing beyond its limit, S(t), S̄_w(t), and Π(t) are marked **unavailable** for that snapshot. (v2의 단일 5일 규칙은 주간 시리즈와 양립 불가 — 구현 검토에서 발견, v3에서 교정.)

### 1.4 Ω live 정렬 규칙 (★ v3 핵심 수정 — 박제)

> **Live archive rule: TOTBKCR is aligned to daily snapshots using only the latest value available as of the snapshot date (LOCF within the §1.3 limit). No interpolation requiring future observations is used in live snapshots.**
>
> Rationale: linear interpolation between weekly observations requires the *next* weekly value, which does not exist at live snapshot time — using it would constitute look-ahead, violating the "as visible on that day" principle (common C4.5). The foundation paper's linear interpolation was valid for its fully retrospective setting but is not causal.
>
> Consequences (인정하고 감): under LOCF the Ω series is a weekly step function at daily resolution. Live P99, μ_control, σ_control are computed from live-rule data, so the specification is self-consistent. Numerical results will differ somewhat from the foundation's interpolated pipeline; this is expected and is not a defect. **Calibration of the live specification uses these live rules end-to-end** (§5), so the calibrated computation is exactly the frozen computation.

## 2. Normalization (★ v3 — 이원화)

`x̂(t) = T(x(t)) / P99` — 단, P99의 출처가 목적별로 다르다:

### 2.1 Live archive P99 (freeze 대상)
| 항목 | 값 |
|---|---|
| live stable reference 기간 | **2024-01-01 ~ 2025-12-31** — `calibration/C-US/live_reference_window_v1.md`에 사전 결정 근거 보존 |
| P99 (숫자 박제) | **ρ = 0.25, Ψ = 0.1999999999999993, Ω = 18958.8656** — live rule(§1.4 LOCF 포함)로 산출하여 v1.0 freeze 시 고정; 이후 재계산 없음 |
| τ₀ | 1/365 (거래일 관측치당) — 확정 ✓ |

### 2.2 Calibration용 event-specific P99 (prospective evidence 아님)
> **Calibration normalization:** each historical event is normalized by a P99 computed from that event's **pre-registered event-specific stable window** (§5.1). This is a usability check of the specification's *structure*, not of the live frozen numbers.
>
> **Live archive normalization:** the live frozen P99 numbers (§2.1) apply only to post-freeze snapshots and are never recomputed.
>
> This separation prevents two failure modes: (a) normalizing 2008-era data with 2020s-regime P99 values (meaningless cross-regime comparison), and (b) the later challenge "is calibration performance the same thing as live-spec performance?" — it is not, and this SPEC says so explicitly.

## 3. Alert (확정 — μ/σ 숫자만 calibration 의존)

| 항목 | 값 | 상태 |
|---|---|---|
| metric | S̄_w(t) = rolling mean of S(t) = ρ̂·Ψ̂·Ω̂ over **w = 90 거래일 관측치** (calendar day ✗ — v3 정밀화) | 확정 ✓ |
| Yellow | S̄_w > μ_control + 2σ_control | 확정 ✓ |
| Red | S̄_w > μ_control + 3σ_control | 확정 ✓ |
| episode cooldown | **10 거래일** (common C6 골격) | 확정 ✓ |
| horizon | **6개월** (episode open일 기준) | 확정 ✓ |
| μ_control, σ_control | **μ = 0.03397769653160021, σ = 0.038047420246019654**, 산출 reference 기간 **2024-01-01 ~ 2025-12-31**, Option B(in-window S̄ with 90-observation burn-in) | **frozen ✓** |
| **live Π 정의** | **Pi_since_freeze** — 적분 원점 = 이 SPEC의 freeze일. freeze 이전 날짜의 Π는 정의되지 않음(NaN). | 확정 ✓ (v4) |

**Π 정의 근거 (박제):** raw cumsum은 fetch 시작점에 따라 절대값이 달라져 "같은 날짜의 공식 Π"가 유일하게 정의되지 않는다. 적분 원점을 freeze일로 고정하면 값이 history 시작점과 무관하게 유일해지고, "동결 이후 누적된 스트레스"라는 아카이브의 의미와 정확히 일치한다. (calibration의 Sep 계산은 window 내 합을 직접 쓰므로 이 정의와 무관.)

**근거 (박제):** w = 90은 foundation의 pseudo-prospective 분석(2008 케이스, 90-d rolling S̄, 2σ threshold)과 동일 구조 — 논문과 아카이브의 방법론 연속성. 2σ/3σ 2단계는 yellow(주의)/red(episode 개시) 구분이며 outcome 판정은 red episode에만 연동(common C7).

## 4. Outcome (frozen v1.0)

| | 정의 | 상태 |
|---|---|---|
| **Primary** | **KBE (SPDR S&P Bank ETF)** open-date anchored 6개월 forward drawdown | **frozen ✓** |
| collapse | drawdown ≥ **25%** | 확정 ✓ |
| correction | **12% ≤ drawdown < 25%** | 확정 ✓ |
| quiet | < 12% | 확정 ✓ |
| **Secondary** | FDIC 은행 파산 이벤트 — horizon 내 **reported total assets ≥ USD 10B**인 파산 발생 | **frozen ✓** |

### 4.1 임계 근거 (박제 — calibration 이전 확정)
> Collapse/correction thresholds (25% / 12%) were fixed **prior to any calibration run**. Rationale: bank-sector equity indices exhibit higher volatility than broad-market indices, so the conventional 20% bear-market threshold is raised to 25% for collapse; the correction floor (12%) is set proportionally above the broad-market convention (10%). These thresholds are frozen and are not adjusted in response to calibration results.

### 4.2 Outcome 소스 요구조건 (common C7 분리 기준 적용)
- 입력 채널: 매일 무인 fetch 생존 필수. **outcome 시리즈: 평가 시점 공개 재구성 가능이면 충분** (매일 snapshot 권장, freeze 요건 아님).
- primary 지수: **KBE (SPDR S&P Bank ETF)**. Secondary market check는 **BKX**, 공개 재현 가능한 소스가 있을 때만 사용. 세부 가격 convention과 평가 규칙은 `calibration/C-US/outcome_definition_v1.md`에 고정.
- 배제 근거(박제): credit spread spike는 입력 Ψ와 영역 중첩(순환성)으로 primary 배제. 은행주 지수는 비입력·시장가격·일별 판정 가능. FDIC 파산은 객관적이나 희귀·이진적이라 secondary.
- 순환성 평가: 입력(금리·spread·은행신용) vs outcome(은행주 가격·파산 이벤트) — 다른 시리즈·다른 영역, 순환성 낮음.

## 5. Pre-freeze calibration (completed audit record)

> common C5 적용: usability check, 성능 증거 아님. **전면 공개**: 모든 사건의 Sep(Π), Sep(S̄), stable max|r|, red episode 수, 결측률 raw 결과를 `calibration/C-US/`에 전부 저장.
> **사전등록 기록:** 아래 window는 `calibration/C-US/calibration_plan.md`에 실행 전 고정되었고, v1 및 v2 결과와 함께 보존된다. Freeze 이후 calibration window 수정은 금지된다.

### 5.1 사건 목록 + event-specific window (v3 — window 사전 고정)

| 구분 | 사건 | 조합·모드 | stable window (P99용) | control / crisis window | 상태 |
|---|---|---|---|---|---|
| Positive | 2008 GFC | historical(재현 모드) **+ live(live rule)** | **2004-01 ~ 2006-12** (foundation Supp T18 상속) | control 2004-01-09~2006-06-30 / crisis 2005-01-05~2009-03-31 (foundation 상속) | **고정 ✓** |
| Positive | 2020 COVID 신용충격 | live | **2014-01-01 ~ 2018-12-31** | control **2017-01-01 ~ 2018-12-31** / crisis **2020-01-01 ~ 2020-06-30** | **고정 ✓** |
| Positive | 2023 SVB | live 단독 | **2021-01-01 ~ 2021-12-31** | control **2021-01-01 ~ 2021-12-31** / crisis **2023-01-01 ~ 2023-06-30** | **고정 ✓** |
| Negative | 2019 repo near-miss | historical + live | **2014-01 ~ 2018-12** (foundation Supp T10 상속) | control **2017-01 ~ 2018-12** / evaluation **2019-01 ~ 2020-02** (foundation 상속) | **고정 ✓** |
| Negative | QUIET_2017 | live | **2014-01-01 ~ 2016-12-31** | control **2015-01-01 ~ 2016-12-31** / evaluation **2017-01-01 ~ 2017-12-31** | **고정 ✓** |

**상속 원칙 (박제):** 2008·repo의 window는 foundation 논문에 **이미 공개된 값**을 그대로 상속 — window 선택이 튜닝 노브가 아님을 공개 이력으로 증명. 신규 사건(COVID·SVB·quiet)의 window는 calibration_plan commit으로 실행 전 고정.

### 5.2 Pass/fail (common C5 골격)
- positive 3개 중 ≥ 2에서 Sep(Π) > 1.0 **및** Sep(S̄) ≥ 1.0 (live 조합 기준)
- negative 전체에서 red episode 0건
- stable 기간 max|r| < 0.7 (live rule 변환 후 ρ↔Ψ↔Ω — 특히 신규 Ψ)
- DCPF3M·DTB3 결측률이 §1.3 fill rule 내 처리 가능함을 확인
- sensitivity 기록: DCPF3M − DGS3MO 버전 동일 지표 (기록 전용, primary 불변경)

### 5.3 TEDRATE ↔ CP–T-bill 정합성 (기록)
중첩 구간(1997~2022-01)에서 두 spread의 상관 + 주요 스트레스 국면(2008·2020) 방향 일치를 문서화 — "기능적 후계" 주장의 실증 근거.

## 6. Freeze completion record (v5)

```text
Freeze completed:
[✓] common v4 + C-US frozen v5 specification recorded
[✓] Ψ = DCPF3M − DTB3; Ω = as-of LOCF; channel-specific fill limits fixed
[✓] calibration event windows fixed and v1/v2 audit results preserved
[✓] LIVE_STABLE_WINDOW = 2024-01-01 ~ 2025-12-31
[✓] LIVE_P99 = {rho: 0.25, psi: 0.1999999999999993, omega: 18958.8656}
[✓] LIVE_MU_SIGMA = {mu: 0.03397769653160021, sigma: 0.038047420246019654}
[✓] primary outcome = KBE; secondary market check = BKX if reproducible
[✓] secondary FDIC threshold = reported total assets ≥ USD 10B
[✓] no-lookahead and snapshot integrity tests passed
[✓] python -m pytest -q = 44 passed
[✓] freeze commit = 68731c6546ebd4845531aac03e1f3be198aab61a
[✓] release tag = c-us-freeze-v1.0

Post-freeze pending:
[ ] first snapshot with snapshot_status = valid
[ ] Zenodo archival and DOI recording
```

The pending items do not alter the frozen analytical rule. DOI metadata will be added only after a DOI is issued.
