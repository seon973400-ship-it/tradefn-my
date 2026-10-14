# 솔루션 킷 점검표 — CP4 15:40 코드 프리즈 → 15:50 `v1.0`

> 저장소 관리자가 15:30부터 본다 · 심사 기준 ③(솔루션 킷 품질)이 이 목록으로 채점된다 · 프롬프트 [P6-9](https://brainini.github.io/tradefin-ai-2026/prompts/day6.html#p6-9)가 이 파일과 저장소를 대조한다 · 사이트 6일차 '솔루션 킷' 페이지와 같은 내용

## 1. README 5항목

- [ ] **1 목적** — 위기 카드 · 한 줄 요약(상황 · 트리거 · 영향 숫자 1개) · 답한 카드 질문 · 반영한 인젝트(I-1 · I-2)
- [ ] **2 구성** — 폴더와 담당
- [ ] **3 실행 방법(재현 절차)** — 새 폴더에서 `uv sync`부터 다시 돌려 확인한 그대로: 어떤 파일로 · 무엇을 실행하면 · 무엇이 나오나(3–5줄) + 쓴 경로(Claude Code / 채팅 AI / 엑셀 근사 / 강사 정답본으로 합류한 단계)
- [ ] **4 데이터 원천과 가상 여부** — 모든 파일이 가상 한빛정밀 데이터 · 원본 파일 이름
- [ ] **5 담당자** — 조-번호 · 역할 · GitHub 아이디(이름 대신 조-번호를 써도 된다)

## 2. 폴더 6개

| 폴더 · 파일 | 들어 있어야 할 것 |
|---|---|
| `README.md` | 5항목 + 위기 카드 요약 · 데모 링크 |
| `data/` | 카드를 반영한 `d6_{카드}_scored.csv` · `d6_{카드}_open_inv.csv` · `change_log.csv`(가상 데이터만) |
| `app/` | `README.md`(배포 주소 · 사용한 커밋 · 바꾼 기능 · 막혔을 때 쓴 경로) · `pipeline/` 스크립트 |
| `sop/` | `SOP_{카드}.md`(0–10장 + 부록) · `ai_usage_rules.md` |
| `roi/` | `roi_kpi.xlsx`(보수 · 기준 · 낙관) |
| `docs/` | `proposal_team.md` · `architecture.md` · `evidence.md` · `decision_log.md` · `demo_script.md` |

도구 폴더(`.claude/` · `.github/` · `tools/`)와 `CLAUDE.md` · `pyproject.toml` · `uv.lock`은 6개에 세지 않는다.

## 3. 보안 점검 — 3검색 (15:40 전)

| # | 무엇을 | 어떻게 | 기준 |
|---|---|---|---|
| 1 | 키 · 비밀값 | 저장소 검색창(Code)에 `sk-` · `AIza` · `ghp_` · `secrets`를 차례로 넣는다. 파일 목록에 `secrets.toml` · `.env`가 없는지도 본다 | 실제 키 0건 |
| 2 | 실명 · 회사명 | 팀원 실명 · 자사 이름 · 실제 거래처 이름 | 0건 |
| 3 | 이메일 | `@`를 찾아 가상 주소(`example.com` · `.example`)만 있는지 | 실제 주소 0건 |

- 내 PC에서는 같은 낱말을 `git grep -nIE`로 한 번에 봅니다(명령은 프롬프트 [P6-9](https://brainini.github.io/tradefin-ai-2026/prompts/day6.html#p6-9) 3단계에 있다). 새 저장소는 GitHub 검색 색인이 늦을 수 있으니 파일 목록도 눈으로 본다.
- **걸린 줄이 있으면 줄마다 이유를 판단한다.** 실제 키 · 실제 이메일은 0건이어야 한다. 검색어를 설명한 글(이 점검표처럼)이나 예시 이름 · 가상 주소 `example`에 걸린 줄은 남아도 되고, 남긴 줄마다 이유를 한 줄 적는다(README 4번 아래).
- 키가 한 번이라도 커밋됐다면 파일을 지워도 이력에 남는다 → 그 키를 폐기하고 새로 받은 뒤 강사에게 알린다. 이력을 덮어쓰는 `force push`는 하지 않는다.
- 협업자(Settings → Collaborators)는 우리 팀원과 강사 계정뿐이다.
- 개인 파일(`d6_plan__…docx` · `d6_roi__…xlsx` · `plan_draft__…`)이 커밋 목록에 없다 — 비공개 폼으로만 낸다.

## 4. `v1.0` 릴리스

릴리스는 **고정해 두는 판**이다 — 태그는 옮기지 않고, 15:50 뒤에 고친 것은 `v1.1`로 낸다. 심사 대상은 `v1.0`이다.

1. 릴리스 노트 `docs/release_v1.0.md` 6절: 이 릴리스에 든 것 · 다시 돌리는 법 · 데이터 · 사람이 승인하는 지점 · 알려진 한계 · `v0.5` → `v1.0` 바뀐 것. 초안은 프롬프트 [P6-3](https://brainini.github.io/tradefin-ai-2026/prompts/day6.html#p6-3)으로 받고 사람이 고친다.
2. 브랜치 `release/v1.0`에 커밋 → PR → **다른 역할 1명이 확인하고 사람이 병합**한다(병합 버튼은 사람이) — 15:40 코드 프리즈 전에.
3. **15:40 코드 프리즈** — 이후에는 기능을 더하지 않는다. README · 오타는 `v1.0`을 만들기 전에만 고친다.
4. 프리즈 뒤 main에서 `gh release create v1.0 --target main --title "v1.0 — {카드 제목} 솔루션 킷" --notes-file docs/release_v1.0.md`. `gh`가 막히면 **GitHub 웹: Releases → Draft a new release → Choose a tag에 `v1.0` 입력 → Target = `main` → Publish release**.
5. 릴리스 주소(`…/releases/tag/v1.0`)를 제출 폼에(15:50).

## 5. GitHub이 막히면

- `d6_team_solution__T{조}.zip`(README 포함, 폴더 구조 그대로)을 USB로 강사에게 건넨다(팀 제출 폼은 파일을 받지 않는다) — 강사가 대신 올리고 감점하지 않는다.

## 6. 제3자 재현 테스트 (심사 기준 ③ 4점)

- [ ] 우리 팀원이 아닌 사람(또는 다른 역할의 팀원)이 **새 폴더**(`git worktree add ../T-verify v1.0` 또는 새 clone)에서 README만 보고 `uv sync`부터 5분 안에 같은 숫자를 낸다. 결과 폴더(`out/`)는 지우고 다시 만들어 비교한다 — 태그가 가리키는 커밋에 결과 파일이 이미 들어 있으면 그대로 돌려서는 재현이 증명되지 않는다.
- [ ] 입력은 저장소 안에 있다 — 우리 카드 `cards/` · 팀 팩과 4일차 입력 `data/input/`(커밋됨). 새 폴더에서 빠진 입력이 있으면 README 3번에 받는 법(`uv run python tools/get_day_files.py 6`)과 둘 자리를 적는다. `local/`의 약관은 재현에 쓰지 않는다.
- [ ] 이슈 · PR 이력이 남아 있다(역할 이슈 5개 · PR 리뷰 1개 이상).
