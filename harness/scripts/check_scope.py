"""편집 범위 검사. 단계가 끝날 때 오케스트레이터가 실행한다.

- 로컬: stage_started_at 이후 바뀐 파일 중 이번 단계 담당이 아닌 번호 폴더에 있는 파일 수
- Figma: page_snapshot과 현재 페이지별 프레임 수를 비교해 이번 단계 담당이 아닌 페이지의 변화 수
사용법: python check_scope.py <실행 폴더> --stage <1|2|3> [--figma-counts <json>]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common as c

# 단계별 담당 에이전트와 Figma 페이지 (roles.md). 폴더는 rules.yaml scope에서 읽는다.
STAGE_AGENTS = {
    1: ["ref-collector", "ref-analyst"],
    2: ["screen-planner"],
    3: ["designer", "guide-reviewer"],
}
STAGE_PAGES = {1: ["01_Reference"], 2: ["02_Screen Spec"], 3: ["03_Design"]}
ALWAYS_PAGES = ["00_Gate Log"]


def check(run, stage, figma_counts_path=None):
    rules = c.load_rules()
    scope = rules["scope"]
    res = c.Result("scope-stage%d" % stage, ["S-01", "S-02"])
    state = c.load_json(os.path.join(run, "state.json"))
    since = float(state.get("stage_started_at") or 0)

    allowed = [d for a in STAGE_AGENTS[stage] for d in scope.get(a, [])]
    owned = sorted({d for a, ds in scope.items() if a != "main" for d in ds})
    for d in owned:
        root = os.path.join(run, d)
        if not os.path.isdir(root) or d in allowed:
            continue
        for base, _, files in os.walk(root):
            for f in files:
                p = os.path.join(base, f)
                if os.path.getmtime(p) > since:
                    res.add("S-01", "담당 밖 폴더 변경: %s" % os.path.relpath(p, run).replace("\\", "/"))

    if figma_counts_path:
        now = c.load_json(figma_counts_path)
        before = state.get("page_snapshot") or {}
        ok_pages = STAGE_PAGES[stage] + ALWAYS_PAGES
        for page in sorted(set(before) | set(now)):
            if page in ok_pages:
                continue
            if before.get(page) != now.get(page):
                res.add("S-02", "담당 밖 Figma 페이지 변경: %s %s → %s" % (page, before.get(page), now.get(page)))
    return res.write(run)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--stage", type=int, required=True, choices=[1, 2, 3])
    ap.add_argument("--figma-counts")
    a = ap.parse_args()
    sys.exit(c.report(check(os.path.abspath(a.run), a.stage, a.figma_counts)))
