---
variant: B
layout: 7일 열 배치
screens:
- id: weekly
  priority:
  - 오늘의 미완료 할 일
  - 주차별 목표 진행률
  - 이번 주 할 일
  fields:
  - name: 오늘의 미완료 할 일
  - name: 진행률
    source_id: SRC-progress
  - name: 완료량
    source_id: SRC-done
  - name: 남은 양
    source_id: SRC-remain
  - name: 미연결
- id: monthly
  priority:
  - 목표 영역별 진행률
  - 주차별 계획량
  fields:
  - name: 진행률
    source_id: SRC-progress
  - name: 완료량
    source_id: SRC-done
  - name: 남은 양
    source_id: SRC-remain
  - name: 인접 월
- id: task-tree
  levels:
  - 월 태스크
  - 주 태스크
  - 일 태스크
  priority:
  - 월 목표
  - 주차별 목표
  - 일간 할 일
  fields:
  - name: 월 목표
  - name: 주차별 목표
  - name: 일간 할 일
delete_confirm:
  fields:
  - affected_tasks_count
  - 미연결로 보존
---

# 화면 설계 B안

목표 영역, 월 목표, 주차별 목표, 일간 할 일을 태스크 단위로 묶어 본다.
