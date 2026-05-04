## 하네스: Mise (소설 이미지 생성 서비스)

**목표:** 소설 텍스트를 입력하면 LLM이 장면을 분석하고 이미지 생성 AI용 프롬프트를 만들어 장면 이미지를 생성하는 서비스 구현

**트리거:** Mise, 소설 이미지, 장면 분석, 이미지 생성, Streamlit, LangChain 관련 개발 작업 요청 시 `mise-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**Git 규칙:** 커밋, 푸시, 브랜치 생성 시 `git-workflow` 스킬을 따르라. main 직접 커밋 금지.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-04 | 초기 구성 | 전체 | - |
| 2026-05-04 | 이미지 생성 API 변경: NVIDIA Sana → Gemini | backend-engineer, mise-backend, mise-orchestrator | 기획 변경 |
