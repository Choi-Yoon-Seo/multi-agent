# Hook / 자동 검증 설계 메모

## 목표
- 응답 완료 시(`Stop` 이벤트 가정) `practice/chapter3/data/output/` 산출물이 비어 있으면 경고를 발생시킨다.

## 제안 훅 동작
- 이벤트: `Stop`
- 검사 명령(크로스플랫폼):
  - macOS: `python3 practice/chapter3/code/run_practice5_hook_check.py`
  - Windows: `py -3 practice/chapter3/code/run_practice5_hook_check.py`
- 기준:
  - 1개 이상이면 통과
  - 0개면 실패 로그를 `practice/chapter3/logs/practice5_hook_check.log`에 기록

## 기대 효과
- 문서 규칙만 둘 때 발생하는 "실행했지만 파일 미생성" 누락을 즉시 발견 가능.
