# To-Do Planner 디자인 하네스

목적: PRD와 대상 화면을 받아 레퍼런스 → 화면 설계 → 디자인 시안 A·B를 Figma에 만들고, 게이트를 통과한 결과를 본인이 컨펌한다.

## 먼저 읽을 것

- 판정 기준: docs/story-service.md (어기면 안 되는 것)
- 디자인 가이드: docs/design.md
- 목적·완료 기준: harness/purpose.md
- 단계·되돌아가기: harness/pipeline.md
- 폴더·파일 형식: harness/artifacts.md
- 역할·편집 범위: harness/roles.md
- 모든 숫자 규칙: harness/rules/rules.yaml (이 파일에 숫자를 옮겨 적지 않는다)

## 트리거

| 사용자 말 | 할 일 |
|---|---|
| "하네스 시작: <화면들>" | 새 실행을 만든다 (아래 "시작") |
| "이어서 해줘" | runs/<최신>/state.json을 읽고 멈춘 단계부터 진행 |
| "게이트 판정해줘" | 현재 단계의 판정을 실행 |
| "A안 컨펌" / "B안 컨펌" | 승인 기록 후 종료 |

## 시작

1. harness/runs/<YYYYMMDD-HHMM>/ 을 만든다.
2. Figma 파일을 새로 만들고 페이지 00_Gate Log, 01_Reference, 02_Screen Spec, 03_Design을 만든다.
3. input.json에 prd_version, screens, figma_file_key, 페이지 node_id를 쓴다. screens는 rules.yaml run 항목으로 검사한다.
4. state.json을 만든다.

## 순서

```text
ref-collector → ref-analyst → gate-judge(gate1)
→ screen-planner(A) ∥ screen-planner(B) → gate-judge(gate2)
→ designer(A) ∥ designer(B) → guide-reviewer
→ 본인 컨펌
```

- 에이전트를 부를 때 실행 폴더 경로와 담당 변형(A/B)을 넘긴다.
- 각 판정 후 gates/*.json 결과를 Figma 00_Gate Log에 프레임 하나로 올리고 state.json을 갱신한다.
- 단계를 시작할 때 state.json에 stage_started_at과 page_snapshot(페이지별 프레임 수)을 쓴다.
- 단계가 끝나면 python harness/scripts/check_scope.py <실행 폴더> --stage <N> --figma-counts <현재 페이지별 프레임 수 JSON>을 실행한다. 위반이 있으면 게이트 판정 전에 사용자에게 보고한다.

## 실패와 멈춤

- 게이트 1 실패: ref-collector부터 다시.
- 게이트 2 실패: screen-planner부터 다시. 원인이 비교표면 ref-analyst부터 다시.
- 가이드 위반이 있으면: guide-reviewer의 review.md를 designer에게 넘겨 고친 뒤 다시 검수.
- 같은 지점 연속 실패가 rules.yaml run.max_consecutive_fail에 닿으면 멈추고 사용자에게 보고한다.

## 컨펌

- 가이드 검수 통과 후 사용자에게 Figma 03_Design 링크를 주고 A/B 중 선택을 묻는다.
- 답을 state.json approved_variant와 00_Gate Log에 기록한다.

## 오케스트레이터가 하지 않는 일

- 레퍼런스, 비교표, 설계 문서, 시안을 직접 만들거나 고치지 않는다.
- 번호 폴더(01~05)에 파일을 쓰지 않는다. 오케스트레이터가 쓰는 곳은 input.json, state.json, Figma 00_Gate Log뿐이다.
- 게이트를 건너뛰거나 판정 결과를 바꾸지 않는다.
