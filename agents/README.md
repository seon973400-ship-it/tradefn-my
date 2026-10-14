# agents — LLM 관문 설정 (강사용 · 선택)

5일차 앱(`app/`)은 LLM 키가 없으면 **모의 모드**로 끝까지 돕니다. 수강생 실습은 키 없이 합니다. 실제 AI 초안을 보여 줘야 할 때만 강사가 아래 LiteLLM 프록시를 세워 개인 키를 나눠 줍니다.

| 파일 | 무엇 | 가져가는 곳 |
|---|---|---|
| [`litellm/config.yaml`](litellm/config.yaml) | LLM 관문 설정 — 별칭 `fast-default` · `fast-backup` · `quality`, 가상 키 예산 표 | 강사 서버 |
| [`litellm/issue_keys.py`](litellm/issue_keys.py) | 가상 키 일괄 발급(강사) — 결과는 저장소 밖에만 | 강사 PC |

- 키는 앱 Streamlit **Secrets** 칸에만 넣습니다(`app/.streamlit/secrets.toml.example` 형식). 저장소 · 채팅창 · 단체방에 붙이지 않습니다.
- 메일은 바이어에게 가지 않습니다 — 앱 ⑤는 승인 뒤 초안(.txt)과 감사로그만 남깁니다(Draft-only).
