# Week 3A 실습 실행 기록

기준 문서: `class/week-03.md`
실행 일시(UTC): 2026-03-29
실행 위치: 프로젝트 루트(`agenticAI/`)

공통 실행 규칙(Windows/macOS):
- macOS: `python3 <script.py>`
- Windows: `py -3 <script.py>` (또는 `python <script.py>`)

## 1) 실습 1: 기존 MCP 서버(도구) 연결/호출

이번 환경에서는 Playwright MCP 서버를 연결 대상으로 사용했다.
짧은 설명:
- 이 실습의 핵심은 "도구를 실제로 2회 이상 호출하고, 호출 흔적을 남기는 것"이다.
- 결과 자체보다 호출 성공/실패 조건과 권한 범위를 확인하는 데 목적이 있다.

실행:
- `npx -y @playwright/mcp@latest --help`
- `npx -y @playwright/mcp@latest --version`

결과:
- 두 호출 모두 성공
- 결과 요약 저장: `practice/chapter3/data/output/practice1_tool_calls.json`
- 실행 로그: `practice/chapter3/logs/practice1_run.log`

관찰:
- 서버 실행 옵션(브라우저, headless, output-dir 등)을 확인함
- MCP 클라이언트와 연결하면 페이지 이동/클릭/스크린샷 등 브라우저 자동화 실습으로 확장 가능

미니 매뉴얼(실습 1 공용):
- 설치(바이브코딩 중심)
1. 프롬프트: `Playwright MCP 실습 환경 점검해줘. node/npm 버전 확인하고, mcp 서버 도움말/버전 확인까지 실행해줘.`
2. 원리: 설치 단계는 "실행 가능한 서버 바이너리 확인"이 핵심이다. 즉, 패키지 설치 자체보다 `실행/응답`이 되는지 먼저 본다.
- 설정(바이브코딩 중심)
1. 프롬프트: `.mcp.playwright.json을 생성하고, headless 모드 stdio 설정으로 맞춰줘.`
2. 원리: 설정 단계는 "클라이언트가 서버를 어떻게 띄우는지"를 고정한다. (`command`, `args`, `transport`)
- 실행(바이브코딩 중심)
1. 프롬프트: `MCP로 페이지 접속, 스냅샷/텍스트 추출을 실행하고 결과를 output, logs에 저장해줘.`
2. 원리: 실행 단계는 에이전트 내부에서 `initialize → tools/list → tools/call` 순서로 진행된다.
3. 검증: 사용자는 결과 파일 존재, 핵심 값(예: 목차 줄수), 실패 로그만 확인한다.
- 프로세스 설명 원칙
1. 중간중간 "지금 어떤 MCP 단계인지(설치/설정/실행/검증)"를 한 줄로 공유한다.
2. 실패 시에는 원인과 재시도 방법만 짧게 남긴다.

실제 Playwright MCP 사용 예시:
1. 바이브코딩 프롬프트 예시
- `https://product.kyobobook.co.kr/detail/S000219302880`에 접속해서 **목차(제1장~)**만 추출해 `practice/chapter3/data/output/practice1_kyobo_toc.md`에 저장해줘. MCP 호출 로그도 함께 남겨줘.
2. 에이전트 내부 MCP 호출 흐름(예)
- `initialize`
- `tools/list`
- `tools/call: browser_navigate` (url=`https://product.kyobobook.co.kr/detail/S000219302880`)
- `tools/call: browser_snapshot`
- `tools/call: browser_evaluate` (목차 텍스트 추출)
3. 산출물 예시
- 목차 파일: `practice/chapter3/data/output/practice1_kyobo_toc.md`
- 실행 로그: `practice/chapter3/logs/practice1_run.log`
- 호출 기록(JSON): `practice/chapter3/data/output/practice1_tool_calls.json`

## 2) 실습 2: 규칙 적용 실습

준비:
- 입력 문서: `practice/chapter3/docs/notes.md`
- 규칙 파일: `practice/chapter3/docs/agent-rules.md`
짧은 설명:
- 규칙을 명시하면 출력 위치, 검증 항목, 불확실성 표기를 일관되게 유지할 수 있다.
- 이 실습은 규칙 기반 작업 프로세스를 고정하는 데 목적이 있다.

바이브코딩 적용(권장):
1. 프롬프트
- `practice/chapter3/docs/agent-rules.md 규칙을 반드시 지켜서 notes.md를 요약해줘. 결과는 practice/chapter3/data/output/summary_with_rules.md에 저장하고, 실행 로그도 남겨줘.`
2. 원리
- 에이전트가 "요청"보다 "규칙 파일"을 우선 참조하도록 고정하면 결과 흔들림이 줄어든다.
- 핵심은 모델 성능이 아니라 출력 경로/검증 형식/불확실성 표기를 프로세스로 강제하는 것이다.
3. 검증 포인트
- 결과 파일이 지정 경로에 생성되었는지
- 검증 항목 3개가 포함되었는지
- `확인 필요` 표기가 있는지

실행:
- macOS: `python3 practice/chapter3/code/run_practice2_compare.py`
- Windows: `py -3 practice/chapter3/code/run_practice2_compare.py`

산출물:
- 규칙 적용 결과: `practice/chapter3/data/output/summary_with_rules.md`
- 비교 JSON: `practice/chapter3/data/output/practice2_comparison.json`
- 실행 로그: `practice/chapter3/logs/practice2_run.log`

결론:
- 규칙 적용 결과에 검증 항목(3개)과 불확실성 표기가 포함됨

## 3) 실습 3: 최소 MCP 서버 직접 만들기

### 3-A. 기본 서버: 파일 목록 조회

구현:
- 서버 코드: `practice/chapter3/code/minimal_mcp_server.py`
- 제공 도구: `list_project_files` (읽기 전용 디렉토리 목록)
- 제한:
  - 프로젝트 루트 밖 접근 차단
  - 잘못된 입력 타입 오류 반환
짧은 설명:
- 복잡한 서버보다, 입력/출력/오류를 명확히 드러내는 최소 서버가 학습에 더 효과적이다.
- 특히 정상 입력과 오류 입력을 분리 테스트해 경계 조건을 확인하는 것이 중요하다.

바이브코딩 적용(권장):
1. 프롬프트
- `읽기 전용 MCP 서버를 만들어줘. list_project_files 도구 하나만 두고, 루트 밖 접근은 차단해줘. 테스트 코드까지 같이 만들어줘.`
2. 원리
- 서버를 크게 만들기보다 "도구 1개 + 명확한 오류 처리"로 시작해야 디버깅 비용이 낮다.
- 특히 경로 검증(루트 밖 차단)이 MCP 보안 경계의 핵심이다.
3. 검증 포인트
- `tools/list`가 정상 응답하는지
- 정상 입력(`practice`)은 성공하는지
- 오류 입력(`../../`)은 차단되는지

테스트 실행:
- macOS: `python3 practice/chapter3/code/test_minimal_mcp_server.py`
- Windows: `py -3 practice/chapter3/code/test_minimal_mcp_server.py`

테스트 케이스:
- 정상 입력: `relative_path="practice"`
- 오류 입력: `relative_path="../../"`

결과:
- 정상 입력: 성공(`ok: true`, 목록 5개)
- 오류 입력: 차단(`허용된 프로젝트 경로 밖 접근은 금지됩니다.`)
- 결과 JSON: `practice/chapter3/data/output/practice3_mcp_test_results.json`
- 실행 로그: `practice/chapter3/logs/practice3_mcp_test.log`

### 3-B. 실제 사례: 프로젝트 메모 관리 MCP 서버

서버 코드: `practice/chapter3/code/memo_mcp_server.py`
제공 도구: `save_memo`(저장), `list_memos`(목록), `read_memo`(읽기)
테스트 결과: 7/7 passed (`practice/chapter3/data/output/practice3_memo_mcp_test_results.json`)

바이브코딩 사용법:

1. 프롬프트
- `프로젝트 메모를 저장/조회하는 MCP 서버를 만들어줘. save_memo, list_memos, read_memo 도구를 제공하고, 테스트도 작성해줘.`
2. 원리
- 실제 업무에서는 파일 목록보다 "업무 데이터(회의록/작업메모)"를 다루는 도구가 가치가 높다.
- 저장/목록/읽기 3단 분리는 CRUD 최소 단위로, 확장성과 검증성이 좋다.
3. `.mcp.json`에 등록
```json
{
  "mcpServers": {
    "memo": {
      "command": "python3",
      "args": ["practice/chapter3/code/memo_mcp_server.py"]
    }
  }
}
```
4. 프롬프트로 사용
- 저장: "회의 내용 메모해줘. 제목 '3주차 회의록', 내용은 MCP 서버 완성, 테스트 통과"
- 목록: "저장한 메모 목록 보여줘"
- 읽기: "가장 최근 회의록 읽어줘"
5. 검증
```bash
python3 practice/chapter3/code/test_memo_mcp_server.py
```

## 4) 실습 4: hook + memory 붙이기

실제 사례(매뉴얼):
1. 목표
- Playwright MCP 실습이 끝나면 `practice/chapter3/data/output/`에 결과 파일이 최소 1개 이상 있어야 한다.

2. Hook 규칙(자동 점검)
- 실행 트리거: 작업 종료 시점(Stop)
- 검사 스크립트:
  - macOS: `python3 practice/chapter3/code/run_practice5_hook_check.py`
  - Windows: `py -3 practice/chapter3/code/run_practice5_hook_check.py`
- 실패 조건: 출력 파일 개수 0개
- 통과 조건: 출력 파일 개수 1개 이상

3. Memory 규칙(지속 문맥)
- 출력 기본 경로는 항상 `practice/chapter3/data/output/`
- 로그 기본 경로는 항상 `practice/chapter3/logs/`
- 검증 순서는 `정상 입력 1회 + 오류 입력 1회 + 파일 존재 확인`

4. 확인 파일
- Hook 결과: `practice/chapter3/data/output/practice5_hook_check.json`
- Hook 로그: `practice/chapter3/logs/practice5_hook_check.log`
- Memory 초안: `practice/chapter3/docs/project-memory-draft.md`

5. 설정 방법(실행 절차)
- Memory 설정 파일 작성/유지:
  - `practice/chapter3/docs/project-memory-draft.md`
- Hook 실행 파일:
  - `practice/chapter3/code/run_practice5_hook_check.py`
- Hook 수동 실행(검증):
  - macOS: `python3 practice/chapter3/code/run_practice5_hook_check.py`
  - Windows: `py -3 practice/chapter3/code/run_practice5_hook_check.py`
- Hook 자동 실행 연결(권장):
  - MCP/에이전트 작업 종료 시점(Stop) 후처리 단계에 위 명령 등록
- 설정 정상 동작 확인:
  - `practice/chapter3/data/output/practice5_hook_check.json`의 `status`가 `pass`인지 확인
- 바이브코딩 프롬프트 예시:
  - `작업이 끝날 때마다 hook check 스크립트를 실행해서 pass/fail을 로그에 남기고, memory 규칙 위반이 있으면 바로 수정해줘.`

## 제출물 체크

검증 결과:
- 실제 파일 존재 확인 완료 (`missing_count=0`, 로그 파일 `6개`)

- MCP 연결 설정 파일: `practice/chapter3/.mcp.json`
- Windows용 MCP 설정 파일: `practice/chapter3/.mcp.windows.json`
- Playwright MCP 설정 예시: `practice/chapter3/.mcp.playwright.json`
- skill/instruction 파일: `practice/chapter3/docs/agent-rules.md`
- 최소 MCP 서버 코드: `practice/chapter3/code/minimal_mcp_server.py`
- 실제 사례 MCP 서버 코드: `practice/chapter3/code/memo_mcp_server.py`
- hook 설계 메모: `practice/chapter3/docs/hook-design.md`
- project memory 초안: `practice/chapter3/docs/project-memory-draft.md`
- 테스트 로그: `practice/chapter3/logs/*.log`
- 비교 결과 문서(JSON): `practice/chapter3/data/output/practice2_comparison.json`
- 실습 1 목차 결과: `practice/chapter3/data/output/practice1_kyobo_toc.md`
- 실습 3 메모 서버 테스트 결과: `practice/chapter3/data/output/practice3_memo_mcp_test_results.json`
- 업데이트 체크리스트: `practice/chapter3/data/output/ch03_checklist.md`

## 실패/제약 기록

- `pip install 'mcp>=1.2.0'`는 네트워크/권한 제약으로 설치 실패 (승인 없는 외부 연결 불가)
