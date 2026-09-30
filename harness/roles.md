# 역할

작성일: 2026-09-30
근거: pipeline.md(단계), artifacts.md(폴더), rules/rules.yaml(판정 기준)

## 작업 에이전트

에이전트 하나가 폴더 하나와 Figma 페이지 최대 한 곳만 편집한다. 폴더는 harness/runs/<실행ID>/ 아래에 있다.

| 에이전트 | 단계 | 편집 폴더 | 편집 Figma 페이지 | 하는 일 |
|---|---|---|---|---|
| ref-collector | 1. 레퍼런스 분석 | 01-ref-collect/ | 01_Reference | UIBowl에서 레퍼런스 10개를 모아 references.json을 쓰고 Figma에 프레임을 만든다 |
| ref-analyst | 1. 레퍼런스 분석 | 02-ref-analysis/ | 없음 | 표현 방식 4개를 비교해 compare.md를 쓴다 |
| screen-planner | 2. 화면 설계 | 03-spec/ | 02_Screen Spec | spec-A.md, spec-B.md를 쓴다 |
| designer | 3. 디자인 제작 | 04-design/ | 03_Design | 시안 A·B를 그리고 figma-*.json, nodes-*.json을 쓴다 |
| guide-reviewer | 3. 디자인 제작 완료 조건 | 05-guide-review/ | 없음 | check_guide.py를 실행하고 review.md에 위반 목록과 수정 지시를 쓴다. 시안은 고치지 않는다 |

## 판정자 (읽기 전용)

- 스크립트: harness/scripts/check_gate1.py, check_gate2.py, check_guide.py. 산출물을 읽기만 하고 결과는 gates/에만 쓴다.
- gate-judge 에이전트: 게이트 1·2 스크립트를 실행하고 결과를 보고한다. 편집 도구가 없다.
- Figma 00_Gate Log에 결과를 올리는 일은 오케스트레이터(메인 세션)가 한다.

## 자연어 트리거

| 이렇게 말하면 | 이렇게 동작한다 |
|---|---|
| "하네스 시작: 주간, 월간" | 새 실행 폴더를 만들고 1단계를 시작한다 |
| "이어서 해줘" | state.json을 읽고 멈춘 단계부터 이어서 한다 |
| "게이트 판정해줘" | 현재 단계의 판정 스크립트를 실행한다 |
| "A안 컨펌" 또는 "B안 컨펌" | 승인 결과를 기록하고 실행을 끝낸다 |

## 편집 범위 강제

- 로컬 파일: Claude Code 훅이 에이전트별 편집 폴더 밖의 쓰기를 막는다. 막힌 편집은 0건이어야 한다.
- Figma: 에이전트 지시문으로 제한한다. 단계가 끝날 때 다른 페이지의 프레임 수가 바뀌지 않았는지 스크립트로 확인한다.
