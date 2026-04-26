# Week 10. 수업 실습: Supervisor 예시

## 1. 예시 과제

- 질문: 2025년 LangGraph 1.0의 주요 변경점을 학부생이 이해할 수 있게 정리한다.
- 목표: Supervisor가 연구자, 분석가, 작성자 중 다음 실행 역할을 동적으로 고른다.
- 최종 출력: 핵심 변경점 3개, 의미, 주의할 점을 포함한 한국어 답변

## 2. 역할 설계

| 역할 | 입력 | 작업 | 출력 | 검증 기준 |
|---|---|---|---|---|
| Supervisor | 현재 state | 다음 역할 결정 | next | 같은 역할만 반복하지 않는가 |
| 연구자 | question | 필요한 사실 정리 | research | 모르는 내용은 확인 필요라고 쓰는가 |
| 분석가 | question + research | 의미와 한계 분석 | analysis | 사실과 해석이 구분되는가 |
| 작성자 | question + research + analysis | 최종 답변 작성 | draft | 학부생이 이해할 수 있는가 |

## 3. 공유 상태

- question: 사용자 질문
- research: 연구자가 정리한 사실
- analysis: 분석가의 해석
- draft: 작성자의 최종 초안
- next: Supervisor가 고른 다음 노드
- messages: 라우팅 로그

## 4. 예상 라우팅

```text
[Supervisor]
   ↓
[연구자]
   ↓
[Supervisor]
   ↓
[분석가]
   ↓
[Supervisor]
   ↓
[작성자]
   ↓
[END]
```

## 5. 예상 라우팅 로그

```text
1. [연구자] 사실 5개 정리 완료
2. [분석가] 분석 완료
3. [작성자] 초안 작성 완료
```

## 6. 실패 조건

1. Supervisor가 연구자만 반복 호출하면 무한 루프가 난다.
2. 분석가가 `RESEARCH_NEEDED`를 남겼는데 Supervisor가 작성자로 보내면 답변 품질이 낮아진다.
3. messages 리듀서가 없으면 라우팅 로그가 누적되지 않는다.

## 7. 5문장 회고

1. Supervisor 패턴은 순서를 고정하지 않고 상태를 보고 다음 역할을 고른다.
2. `Command(goto=...)`는 에이전트 간 핸드오프를 코드로 표현한다.
3. 구조화 출력은 Supervisor의 결정을 문자열 파싱보다 안정적으로 만든다.
4. `recursion_limit`은 잘못된 라우팅이 무한 반복되는 것을 막는다.
5. 9주차 설계표의 역할과 공유 상태가 10주차 코드의 노드와 state로 바뀐다.
