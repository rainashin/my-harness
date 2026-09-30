# 산출물

작성일: 2026-09-30
근거: pipeline.md(단계별 입력·출력), purpose.md(완료 기준)

## 폴더 구조

한 번 실행할 때마다 실행 폴더를 하나 만든다. 번호 폴더 하나에는 에이전트 하나만 쓴다(roles.md).

```text
harness/runs/<실행ID: YYYYMMDD-HHMM>/
  input.json               # PRD 버전, 대상 화면 목록
  01-ref-collect/
    references.json        # 레퍼런스 10개 (ref-collector)
    figma-ref.json         # 01_Reference 페이지 프레임 목록 (ref-collector)
  02-ref-analysis/
    compare.md             # 표현 방식 비교표 (ref-analyst)
  03-spec/
    spec-A.md              # (screen-planner)
    spec-B.md
  04-design/
    figma-A.json           # 변형별 프레임 ID (designer)
    figma-B.json
    nodes-A.json           # 가이드 판정용 노드 추출본
    nodes-B.json
  05-guide-review/
    review.md              # 위반 목록과 수정 지시 (guide-reviewer)
  gates/
    gate1.json
    gate2.json
    guide.json             # Figma 00_Gate Log에도 올린다
  state.json               # 진행 상태
  blocked.log              # 훅이 막은 편집 기록
```

## 형식 원칙

- 사람이 읽는 문서(compare.md, spec-*.md, review.md)는 마크다운으로 쓰고 맨 위에 YAML 앞머리를 둔다. 스크립트는 앞머리만 센다.
- 스크립트가 세는 대상(references.json, nodes-*.json, gates/*.json, state.json)은 JSON으로 쓴다.

## 파일별 필수 항목

| 파일 | 필수 항목 |
|---|---|
| input.json | prd_version, screens(1~4개. weekly, monthly, goal-edit, task-tree 중에서 고른다), figma_file_key, pages(00~03의 node_id). 오케스트레이터가 쓴다 |
| references.json | references: 항목마다 id, url(UIBowl), screen_type(input.json screens 값), reason |
| figma-ref.json | page, frames(항목마다 id, name). Figma 메타데이터에서 추출 |
| compare.md 앞머리 | methods(4개). 방식마다 name, pros(목록), cons(목록), refs(레퍼런스 id 목록) |
| spec-A.md, spec-B.md 앞머리 | variant, layout, screens(화면마다 id, priority(목록), fields(항목마다 name, 지표 항목은 source_id)). task-tree 화면은 levels(3개). delete_confirm.fields |
| figma-A.json, figma-B.json | variant, frames(화면별 frame node_id). file_key와 pages는 input.json에 있다 |
| nodes-A.json, nodes-B.json | variant, frames(id, name, width, height), nodes(id, name, type, frame, width, height, cornerRadius, itemSpacing, padding, fills, strokes, textColor, bg, fontSize, characters). 이름 규칙: 분류색 노드는 cat/로 시작, 완료 표시 노드는 completed 포함, 라벤더 노드는 button 또는 focus 포함 |
| gates/*.json | gate, passed(true/false), date, violations(규칙 ID별 개수), attempt |
| state.json | run_id, stage(1~3), stage_started_at(유닉스 초), last_passed_gate, fail_count(gate1, gate2, guide), page_snapshot(단계 시작 시 페이지별 프레임 수), approved_variant |

## 규칙 SSOT

- 파일: harness/rules/rules.yaml 하나. 모든 숫자 규칙을 여기에만 적는다.
- 토큰 허용값은 복사하지 않는다. 스크립트가 실행할 때마다 docs/design.md 앞머리에서 읽는다.
- 에이전트 지시문과 스크립트에 규칙 숫자를 직접 적은 곳은 0개여야 한다.
- 내용은 R5 게이트 라운드에서 확정한다.

## 재개

- 가능하다. 다시 시작하면 state.json을 읽고, last_passed_gate 다음 단계부터 진행한다.
- fail_count는 이어서 센다. 같은 지점에서 3회 연속 실패하면 멈추고 본인에게 넘긴다.
