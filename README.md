pi-prospective-archive

Π 프레임워크의 사전등록(pre-registered) prospective 검증 아카이브 — C-US (미국 신용 섹터)

이 저장소는 곱셈형 스트레스 지수 Π = ρ × Ψ × Ω 의 진단 규칙을 미리 동결(freeze)하고, 그 이후의 시장 데이터를 매일 자동으로 기록하여 "결과를 보고 사후에 규칙을 맞춘 것이 아님"을 시간 순서로 증명하기 위한 증거 아카이브입니다.


이 저장소가 무엇인가 / 무엇이 아닌가

이것은:


사전등록된 진단 프레임워크(pre-registered diagnostic framework)의 운영 기록
채널 정의·정규화 상수·경보 규칙·성과 판정 기준을 freeze 시점에 고정하고, 이후 변경하지 않는 불변 아카이브
매일 "그날 실제로 보였던" 원본 데이터(point-in-time vintage)를 append-only로 박제하는 저장소


이것이 아닌 것:


❌ 예측 서비스 또는 투자 신호 — 경보(alert)는 연구 기록이며, 이 저장소의 어떤 내용도 투자 조언이 아닙니다.
❌ 정확한 확률 모형 — Π는 parameter-free 진단(diagnostic) 지수입니다.
❌ 가변 분석 환경 — freeze 이후 동결된 정의는 수정되지 않습니다. 변경이 필요하면 새 SPEC 버전으로 분기합니다.


현재 상태

항목상태C-US (미국 신용 섹터)dry-run 단계 — 파이프라인 시운전 중. 현재 쌓이는 snapshot은 dry_run 신분이며 평가에서 제외됩니다Prospective 증거 시작아직 아님. C-US SPEC freeze commit 시점부터 시작됩니다M-KR (한국 시장 섹터)보류 — 데이터 소스 안정성 확정 후 별도 시계로 시작

Prospective 증거는 각 subtrack의 SPEC freeze 시점부터만 인정됩니다. freeze 이전의 모든 기록(dry_run, calibration)은 시운전·적합성 점검이며 prospective 증거로 계산되지 않습니다. 이 원칙은 SPEC 문서에 명문화되어 있습니다.

핵심 설계 원칙


사전동결 + 시간순서 — 변수·정규화·경보·판정 규칙을 미래 사건이 일어나기 전에 고정하고 타임스탬프로 박제. 사후 적합(post-hoc fitting)이 물리적으로 불가능한 구조.
Point-in-time 원칙 — raw 층은 그날 fetch된 원본 값을 그대로 기록. 데이터 제공자의 사후 수정(revision)은 이후 snapshot에만 나타나며, 과거 snapshot은 절대 재계산·수정되지 않음.
인과적 계산 (no-lookahead) — 어떤 계산도 미래 관측치를 사용하지 않음. "시점 t에서 데이터를 절단해 계산한 값 = 전체 데이터 계산의 t 이전 값"이 단위 테스트로 상시 검증됨.
Append-only — force-push·브랜치 삭제 차단. 정정(correction)은 과거 수정이 아니라 새 run으로 추가되며, 사유는 통제 어휘(controlled vocabulary)로 제한.
전면 공개 — calibration의 통과/탈락 판정뿐 아니라 모든 원시 지표를 공개. 은폐 없음.


저장소 구조

SPEC-1.0_common_v4.md      ← 공통 운영 헌법 (인과성·correction·검증 규칙)
SPEC-1.0-C-US_v5.md        ← C-US subtrack 헌법 (채널·경보·판정 정의)
src/pi_archive/            ← 계산·기록 코드 (SPEC의 기계적 표현)
tests/                     ← 불변량 테스트 (인과성·append-only·계약 검증 등)
.github/workflows/         ← 자동화: CI / 일일 수집 / health check
snapshots/C-US/{날짜}/{run}/  ← 일일 snapshot (raw / computed / alert / meta / manifest)

각 snapshot은 5개 파일로 구성됩니다: raw.csv(그날 보인 원본), computed.csv(동결 규칙으로 계산된 값 + 계산 가능 여부 상태), alert.json(그날의 경보 레벨), meta.json(계산에 쓰인 상수·코드 commit·환경 hash 박제), manifest.sha256(파일 무결성).

Snapshot 검증 방법 (감사자용)

누구든 다음을 확인할 수 있습니다:

bashgit clone https://github.com/Junwon03/pi-prospective-archive
cd pi-prospective-archive
pip install -r requirements.lock
python -m pytest -q                    # 전체 불변량 테스트


무결성: 각 run 폴더의 manifest.sha256로 파일 hash 재검증 가능
재현성: raw.csv + meta.json의 상수(p99_used 등)만으로 computed.csv 완전 재생성 가능
계산 맥락: meta.json의 code_git_commit이 해당 snapshot을 생성한 정확한 코드 버전을 가리킴
환경: environment_hash가 requirements.lock을 가리켜 실행 환경 고정


정정(correction) 처리

잘못된 run은 삭제하지 않습니다. 새 correction run이 supersedes 포인터로 이전 run을 가리키며 추가되고, 사유는 통제 어휘(FRED_API_OUTAGE, PARTIAL_FETCH_FAILURE 등)로 제한됩니다. 평가 시에는 각 날짜의 최신 유효 run만 사용하되 이전 run도 영구 보존됩니다.

데이터 출처

모든 입력은 FRED(Federal Reserve Economic Data)의 공개 시리즈입니다: DFF, DCPF3M, DTB3, TOTBKCR. 채널 정의와 선택 근거는 SPEC-1.0-C-US_v5.md §1에 명시되어 있습니다.

인용

정식 인용은 freeze 이후 분기별 Zenodo 릴리스(불변 DOI)를 통해 제공될 예정입니다. 그 전까지는 이 저장소의 URL과 commit hash로 참조해 주십시오.


저자 및 기여

아이디어, 연구 설계, 방법론적 결정, 최종 검증의 책임은 전적으로 저자에게 있습니다.

코드 작성 및 문서화는 다음 AI 모델의 지원을 받아 이루어졌습니다:


Anthropic Claude Fable 5 — 아키텍처 설계 지원, 코드 작성, 테스트 스위트 구축
OpenAI GPT-5.5 Pro — 설계 검수, 결함 탐지, 코드 패치


두 모델의 산출물은 상호 교차 검증을 거쳤으며, 모든 설계 판단과 채택 여부는 저자가 결정했습니다.


This archive is a research record. Nothing in this repository constitutes investment advice.
