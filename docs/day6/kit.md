---
title: 6일차 솔루션 킷
---

<div class="tf-hero tf-hero--sm" markdown>
<span class="tf-eyebrow">6일차 · 솔루션 킷 = 팀 저장소 `v1.0` <span class="tf-daystate" data-tf-daystate="6"></span></span>

# 솔루션 킷 — 다른 사람이 다시 돌릴 수 있게

오늘의 최종 산출물인 **AI 기반 무역 금융 리스크 관리 통합 파이프라인 솔루션 킷**을 이 과정에서는 **팀 저장소 하나**로 냅니다. 처음 보는 사람이 **README만 보고 5분 안에 다시 돌릴 수 있어야** 하고, 제출은 **릴리스 `v1.0`**으로 고정합니다 → 이론은 [이론 요약 2장](theory.md#ch2), 단계는 [실습 B Step 6](lab-b.md#b-release).
</div>

| 킷이 담는 결과물 | 킷 안의 자리 | 담당 |
|---|---|---|
| SOP 매뉴얼 | `sop/SOP_{카드}.md` + `sop/ai_usage_rules.md` | ⑤ · ④ |
| ROI 산출서 | `roi/roi_kpi.xlsx`(팀 ROI 3안) | ③ |
| 도입 기획서 | `docs/proposal_team.md`(팀 요약 2쪽) + 개인 자사판 기획서(비공개 폼 → [제출](submit.md#personal)) | ⑤ · 개인 |
| 스트레스 테스트 | `data/` · `out/{카드}/`(등급 변동표 · 한도안 · EL 표 · 경보) · `docs/decision_log.md` + 7분 데모 | ① – ③ |

## 팀 저장소 만들기 — 5일차 17:31 {#create}

어제 이미 만들었다면 건너뜁니다.

1. **조장**: 킷 템플릿 저장소 [`brainini/tradefin-kit-template`](https://github.com/brainini/tradefin-kit-template) → **Use this template** → **Create a new repository** → 이름 `tradefin-kit-T{조}`(예: `tradefin-kit-T2`) · **Private**(비공개 — 가상 데이터만 둡니다) → **Create repository**. 규정 `rules/hanbit_credit_policy.md` · 점검표 · SOP 양식 · 파일 받기 도구가 이미 들어 있습니다.
2. **조장**: **Settings** → **Collaborators** → **Add people** → 팀원과 강사의 GitHub 아이디로 초대합니다. 무료 계정의 비공개 저장소에서도 이슈 · PR · 리뷰 · 릴리스는 됩니다 — 보호 브랜치가 없으니 '다른 역할 1명 리뷰 뒤에 사람이 병합'을 `CLAUDE.md`와 점검표로 지킵니다.
3. **팀원**: 초대를 수락하고 `README.md` **5. 담당자** 표에 내 줄(조-번호 · 역할 · GitHub 아이디 — 실명 · 회사명 · 이메일 금지)을 더하는 **브랜치 + PR**을 엽니다.
4. **다른 팀원**: PR에 리뷰 코멘트 1개 이상 → **Approve** → **Merge pull request**.
5. 내 PC에서는 VS Code로 `Git: Clone` → 폴더 열기 → **'신뢰'** → `uv sync` → Claude Code 로그인(모드 표시기가 Auto면 Plan으로).

- 조장이 6일차의 **저장소 관리자**입니다(README · 릴리스 책임, 역할과 겸임).

## 폴더 구조 {#structure}

<figure markdown="span">
  ![킷 템플릿의 파일 목록 — 폴더 .claude · .github · app · data · docs · roi · sop · tools, 파일 .gitignore · .python-version · CLAUDE.md · README.md · pyproject.toml · uv.lock 등. GitHub 화면이라 영어 표기](../assets/screens/d6-kit-template-files.png){ width="560" loading=lazy }
  <figcaption>킷 템플릿의 파일 목록(GitHub 화면이라 영어) — 이 아래에 README가 그려집니다</figcaption>
</figure>

| 경로 | 들어 있는 것 | 누가 · 언제 |
|---|---|---|
| `README.md` | 5항목: 목적 · 구성 · 실행 방법(재현 절차) · 데이터 원천과 가상 여부 · 담당자 | 저장소 관리자 · CP1 골격 → CP4 완성 |
| `CLAUDE.md` · `.claude/settings.json` | AI가 세션마다 먼저 읽는 팀 규칙(+ 우리 팀 규칙 3줄) · 권한 allow(`uv run` · `git diff`) · deny(`.env` 읽기 · `git push --force`) | 전원 · 10:11 |
| `pyproject.toml` · `uv.lock` | 환경 — `uv sync` 한 번이면 누구나 같은 버전(Python 3.13) | 킷에 들어 있다 |
| `cards/` | 우리 팀 위기 카드 | RA · 09:28 |
| `data/input/` | 우리 팀 팩 · 4일차 입력 4개 · 환율 파일 — 읽기만(커밋해 두어 새 폴더 재현이 그대로 된다) | RA · 09:28 |
| `data/` | ① 카드를 반영한 결과 `d6_{카드}_scored.csv` · `_open_inv.csv` · `change_log.csv`(가상 데이터만) | ① · CP2 |
| `app/pipeline/` | 파이프라인 스크립트 + `README.md`(단계별 받는 파일 · 내는 파일 계약) | ① – ③ · CP2 – CP3 |
| `out/{카드}/` | 스크립트가 낸 결과 — 등급 변동표 · 한도 변경안 · EL 표 · 경보 · 인젝트 계산 | 스크립트 |
| `rules/` | 가상 여신관리규정(근거표의 원문 — 킷에 들어 있다) | ④ |
| `sop/` | `SOP_template.md` → `SOP_{카드}.md`(0–10장 + 부록) · `ai_usage_rules.md`(1쪽) | ⑤ · ④ · CP3 – CP4 |
| `roi/` | `roi_kpi.xlsx` — 우리 카드 ROI 완성본(보수 · 기준 · 낙관 + 민감도) | ③ · CP3 |
| `docs/` | `architecture.md` · `evidence.md` · `decision_log.md` · `demo_script.md` · `proposal_team.md` · `kit_checklist.md` | ⑤ · ④ · CP1 – CP4 |
| `tools/` | `get_day_files.py`(그날 파일 받기) · `fonts/`(차트 한글 글꼴) | 킷에 들어 있다 |
| `.github/` | 이슈 양식(역할 · 버그) · PR 양식 | 킷에 들어 있다 |
| `.gitignore` | 비밀값 · 개인 파일(`d6_plan__*` · `d6_roi__*`) · `local/` · `data/checkpoints/` · `labs/` · `.venv/` | 킷에 들어 있다 |
| `local/` | 각자 받은 K-SURE 약관(재배포 금지 — 커밋되지 않는 폴더) | ④ |
| Releases | `v0.5`(CP2 · 11:45) · `v1.0`(CP4 · 15:50 제출) + 릴리스 노트 | 저장소 관리자 |

- 개인 도입 기획서 · 개인 ROI 시트 · 사후 진단은 **저장소에 올리지 않습니다** — 비공개 폼으로 냅니다 → [제출](submit.md#personal).
- `get_day_files.py`가 받은 폴더(`data/checkpoints/` · `labs/`)와 K-SURE 약관(`local/`)은 `.gitignore`에 있어 커밋되지 않습니다 — 그래서 파이프라인이 읽는 입력은 `data/input/`에 복사해 커밋합니다(새 폴더 재현이 그대로 됩니다). 비밀값은 작업 폴더에 두지 않는 것이 가장 확실한 잠금입니다.

## README 5항목 — 심사 기준 ③ {#readme}

| 항목 | 무엇을 쓰나 | 예(형식만) |
|---|---|---|
| 1. 목적 | 카드 번호 · 제목 · 한 줄 요약(상황 · 트리거 · 영향 숫자 1개) · 답한 질문 · 반영한 인젝트 | "카드 ② — 대상 바이어 n곳의 EL이 S0 대비 □배(`out/2/el_table.md`)" |
| 2. 구성 | 폴더마다 무엇이 있고 누가 맡았나(템플릿 표를 채운다) | `data/` — 카드 반영 결과 · ① |
| 3. 실행 방법(재현 절차) | **3–5줄** — 어떤 파일로 → 무엇을 실행하면 → 무엇이 나오나 + 사용한 경로. **새 폴더에서 `uv sync`부터 다시 돌려 확인한 그대로** · 입력 위치(`cards/` · `data/input/`) | "`uv sync` → 입력은 `data/input/`(커밋됨) → `uv run python app/pipeline/01_apply.py` → `data/d6_2_scored.csv`" |
| 4. 데이터 원천과 가상 여부 | 파일 · 원천 · 가상 여부 + 보안 점검 확인 시각 · 확인한 사람 | `data/…` — 과정 데이터 팩 · 가상 |
| 5. 담당자 | 조-번호 · 역할 · GitHub 아이디 | `T2-07` · ③ · `@아이디` |

- **재현 절차**는 남이 5분 안에 같은 결과를 내는 절차서입니다. '저장소 소개 글'이 아닙니다.
- 체크포인트에 못 미쳐 강사 정답본으로 합류했다면 3번 '사용한 경로'에 그대로 적습니다 — 감점하지 않습니다.
- 숫자 예의 □ · n은 자리표시입니다. 팀의 실제 결과로 채웁니다.

## 이렇게 일합니다 — 이슈 → PR → 릴리스 {#workflow}

| 단계 | 언제 | 하는 일 |
|---|---|---|
| 이슈로 나누기 | 09:26–09:31(가동 8단계 설명 직후) · Step 2에서 확정 | 역할 ①–⑤마다 이슈 1개(양식 **역할 (해커톤)**): 미션 · 받는 것 → 넘길 것 · 넘길 시각 · 사람이 결정할 항목 · 완료 체크 · 코칭 대행자 |
| 설계도 | 10:11–10:40 | 가동 8단계 × 역할 × 입력 × 넘길 산출물 × 시각 → `docs/architecture.md` · README 골격 = **CP1** |
| 조각 합치기 | 하루 내내 | 작업 하나 = 이슈 하나 = 브랜치 하나 = PR 하나. SOP · README · `data/`처럼 큰 변경은 **PR**로 올리고 **다른 역할 1명이 보고 사람이 병합**. 오탈자는 바로 커밋해도 됩니다. 한 사람이 두 역할이면 [worktree](lab-a.md#a-worktree) |
| 중간 고정 | 11:45 | 태그 `v0.5`(재등급 · 한도 결과, 인젝트 I-1 반영 여부) = **CP2** |
| 사람 결정 기록 | 13:15 이후 | 인젝트 I-2의 결정 · 근거 · 결정자를 `docs/decision_log.md`에 |
| 최종 고정 | 15:40–15:50 | 코드 프리즈 → **CP4**(README 5항목 · 보안 점검 확인) → **`v1.0` 릴리스** + 릴리스 노트 → 새 폴더 재현 · 15:50 링크 |

**웹에서 PR 올리기**: 파일 → 연필 아이콘 → 고친 뒤 **Commit changes** 창에서 **Create a new branch for this commit and start a pull request** → **Propose changes** → PR 양식(무엇을 · 왜 · 관련 이슈 `Closes #번호` · 올리기 전 확인 5) → **Create pull request** → 리뷰어 1명이 **Files changed**에서 확인 → **Merge pull request**.

## 스트레스 테스트를 킷에 남기는 법 {#stress-test}

스트레스 테스트 = 극단적이지만 있을 법한 충격으로 **어디가 먼저 깨지는지** 보는 것입니다. 킷에는 그 흐름이 파일로 남아야 합니다.

| 흐름 | 남는 곳 |
|---|---|
| 카드 → 바뀐 데이터 | `data/d6_{카드}_scored.csv` · `d6_{카드}_open_inv.csv` · `change_log.csv` |
| 바뀐 등급 · 한도 · EL | `out/{카드}/grade_changes.csv` · `limits_diff.csv` · `el_table.md` |
| 경보와 먼저 깨진 곳 | `out/{카드}/alerts.csv` · `docs/decision_log.md` · 인젝트 대응 기록 |
| 대응 절차 | `sop/SOP_{카드}.md` |
| 도입 효과 | `roi/roi_kpi.xlsx` · `docs/proposal_team.md` |

<figure markdown="span">
  ![가동 8단계와 시나리오 S0–S4의 격자 — 충격이 클수록 더 앞 단계 칸이 먼저 깨짐으로 표시된다. 가상 예시](../assets/diagrams/d6-stress-grid.png){ width="480" loading=lazy }
  <figcaption>충격 × 단계 — 어디가 먼저 깨지는지는 시스템마다 다릅니다(가상 예시). 먼저 깨지는 곳 목록과 고칠 순서가 결과물입니다</figcaption>
</figure>

## 보안 점검 — CP4 전에 꼭 {#security}

**3검색**: 저장소 위쪽 검색창(키보드 `/`)에 아래 세 가지를 차례로 넣고 **이 저장소** 결과를 봅니다. 결과가 늦게 뜨면 파일을 직접 열어 확인합니다.

| # | 검색어 | 기준 |
|---|---|---|
| 1 | 키 · 비밀값 — `sk-` · `AIza` · `ghp_` · `secrets`, 파일 목록에 `secrets.toml` · `.env`가 없는지 | 실제 키 0건 |
| 2 | 실명 · 회사명 — 팀원 실명 · 자사 이름 · 실제 거래처 이름 | 0건 |
| 3 | 이메일 — `@`를 찾아 가상 주소(`example.com` · `.example`)만 있는지 | 실제 주소 0건 |

내 PC에 clone했다면 `git grep -nIE "sk-|AIza|ghp_|@"`로 한 번에 봅니다.

**걸린 줄은 줄마다 이유를 판단합니다.** 검색어를 설명한 글(점검표 자신) · 예시 이름 · 가상 주소 `example`에 걸린 줄은 남아도 되고 줄마다 이유를 한 줄 적습니다. **실제 키 · 실제 이메일은 0건**이어야 합니다.

<div class="tf-checklist" data-title="보안 점검" markdown>

- [ ] `data/`에는 가상 한빛정밀 데이터만 있다(회사 실데이터 · 익명화본도 올리지 않는다)
- [ ] **Settings** → **Collaborators**: 우리 팀원과 강사 계정뿐이다
- [ ] 키가 한 번이라도 노출됐다면 이미 **교체**했다(파일을 지워도 커밋 이력에 남는다 — `force push`로 덮지 않는다)
- [ ] `local/`(약관) · `.env` · 개인 파일(`d6_plan__…` · `d6_roi__…`)이 커밋 목록에 없다
- [ ] AI 사용 규칙서 `sop/ai_usage_rules.md`가 있다

</div>

## 릴리스 `v0.5` · `v1.0` 만들기 {#release}

릴리스는 **고정해 두는 판**입니다 — 태그는 옮기지 않고, 15:50 뒤에 고친 것은 `v1.1`로 새 릴리스를 만듭니다. 심사는 `v1.0` 기준입니다. 커밋 = 세이브 포인트, 태그 = 이름 붙인 세이브 포인트, 릴리스 = 태그 + 설명 + 첨부입니다.

**명령(권장)** — 브랜치 `release/v1.0`에 릴리스 노트 `docs/release_v1.0.md`를 커밋하고 PR을 열어 **사람이 병합**한 뒤(15:40 전), 15:40 코드 프리즈가 지나면:

```text
git switch main
git pull
gh release create v1.0 --target main --title "v1.0 — {카드 제목} 솔루션 킷" --notes-file docs/release_v1.0.md
```

**웹 화면(`gh`가 막힐 때)**

1. 저장소 첫 화면 오른쪽 **Releases** → **Draft a new release**(처음이면 **Create a new release**).
2. **Choose a tag** 칸에 `v1.0`을 입력 → **Create new tag: v1.0 on publish**. 대상(Target)은 `main`.
3. **Release title**: `v1.0 — {카드 제목} 솔루션 킷`.
4. 설명 칸에 릴리스 노트를 붙입니다. 초안은 [P6-3](../prompts/day6.md#p6-3)(커밋 목록 · README · 폴더 목록을 넣는다)으로 받고 사람이 고칩니다 — 6절: 이 릴리스에 든 것 · 다시 돌리는 법 · 데이터 · 사람이 승인하는 지점 · 알려진 한계 · `v0.5` → `v1.0` 바뀐 것.
5. `v0.5`는 **Set as a pre-release**, `v1.0`은 **Set as the latest release**를 고릅니다.
6. **Publish release** → 주소 `https://github.com/{아이디}/tradefin-kit-T{조}/releases/tag/v1.0`을 복사해 <span data-tf-link="team_form">팀 제출 폼</span>에 붙입니다([제출](submit.md#team)).

**재현 테스트(제3자 5분)** — 다른 역할 한 명이 새 폴더에서 다시 돌립니다.

```text
git fetch --tags
git worktree add ../T-verify v1.0
cd ../T-verify
uv sync
# 입력 확인 — cards/ · data/input/ 은 커밋돼 따라온다(빠진 것이 있으면 README 대로 get_day_files.py 6 → 같은 자리)
# 결과 폴더(out/)를 지우고 README의 실행 방법대로 다시 돌린 뒤 처음 폴더의 같은 파일과 비교
```

태그가 가리키는 커밋에는 결과 폴더가 이미 들어 있어 그대로 돌리면 같은 파일을 덮어쓸 뿐입니다 — **지우고 다시 만들어 비교해야** 재현이 증명됩니다. 입력을 빼먹으면 스크립트가 빠진 파일 이름을 알리고 멈춥니다.

## 7분 데모 구성 {#demo}

| 시간 | 내용 | 보여 줄 곳 |
|---|---|---|
| 0:00–0:40 | **위기 요약** — 상황 · 트리거 · 영향 숫자 1개(결론 먼저) | README 1번 |
| 0:40–3:00 | **라이브 데모** — 데이터 갱신 → 재등급 → 한도 · EL → 경보 → 근거 → 초안(DRY RUN) | `out/{카드}/` · 저장소 |
| 3:00–4:30 | **SOP 핵심**(T+0 … T+1주, 사람 승인 지점) + 인젝트 대응 | `sop/SOP_{카드}.md` · `decision_log.md` |
| 4:30–5:45 | **ROI · KPI** — 보수안부터, 재무 AI ROI 중앙값 10%와 비교 | `roi/roi_kpi.xlsx` |
| 5:45–6:30 | **솔루션 킷** — README 재현 절차 · 릴리스 | 저장소 · Releases |
| 6:30–7:00 | **도입 첫 30일과 요청 사항** | `proposal_team.md` |
| 질의응답 3분 | 심사위원 2문 + 청중 1문 — 숫자와 근거 파일로 답한다 | 근거표 · 파일 |

- **6:30 노란 카드, 7:00 컷**. 팀원 전원이 한 번 이상 말합니다.
- 대본은 [P6-4](../prompts/day6.md#p6-4)로 받아 `docs/demo_script.md`에 둡니다. 라이브가 실패하면 **60초 녹화 · 캡처**로 바로 바꿉니다(영상은 발표 PC로 옮기고 저장소에는 올리지 않습니다).
- 발표 순서는 15:45에 추첨하고, 16:05부터 10분 간격(데모 7분 + 질의응답 3분)으로 진행합니다.

## 킷 체크리스트 — CP4 15:40 → 15:50 {#checklist}

<div class="tf-checklist" data-title="CP4 15:40 → 15:50 — 링크를 내기 전에" markdown>

- [ ] README 5항목(목적 · 구성 · 실행 방법 · 데이터 원천과 가상 여부 · 담당자)
- [ ] 폴더 6개가 제자리(README · data · app · sop · roi · docs)
- [ ] `data/` — `d6_{카드}_scored.csv` · `d6_{카드}_open_inv.csv` · `change_log.csv`
- [ ] `sop/` — `SOP_{카드}.md` 0–10장(P6-2 검증 반영) · `ai_usage_rules.md`
- [ ] `roi/` — `roi_kpi.xlsx`(우리 카드 완성본 · 보수안부터 3안 · 민감도 1줄)
- [ ] `docs/` — `architecture.md` · `evidence.md` · `decision_log.md` · `demo_script.md` · `proposal_team.md`
- [ ] 역할 이슈 5개 · PR 이력
- [ ] 보안 점검 3검색(실제 키 0건) · 협업자 확인
- [ ] `v0.5`(CP2) · `v1.0` + 릴리스 노트
- [ ] 팀 밖의 한 사람이 새 폴더에서 README만 보고 5분 안에 재현했다

</div>

## 킷 파일 {#files}

--8<-- "docs/_snippets/day6/files_kit_cards.md"

- SOP 양식은 팀 저장소의 `sop/SOP_template.md`와 같은 내용입니다. 팀 저장소에서는 그 파일을 복사해 씁니다. 점검표(`kit_checklist.md`)도 팀 저장소 `docs/`에 이미 들어 있습니다.
- 기획서 양식 `ax_proposal_template.md`의 7–11장은 프롬프트 [S8](../prompts/day6.md#s8)이 `.docx`로 바로 만들어 줍니다 → [기획서 11장](submit.md#proposal).
