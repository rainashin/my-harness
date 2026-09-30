"""게이트 2: 화면 설계 → 디자인 제작. 규칙은 rules.yaml gate2."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common as c


def screen_map(fm):
    return {s.get("id"): s for s in (fm.get("screens") or []) if isinstance(s, dict)}


def field_names(screen):
    return [f.get("name") for f in (screen.get("fields") or []) if isinstance(f, dict)]


def check(run):
    rules = c.load_rules()
    g = rules["gate2"]
    variants = rules["run"]["variants"]
    res = c.Result("gate2", c.rule_ids(g))
    screens_in = c.load_json(os.path.join(run, "input.json")).get("screens", [])

    specs = {}
    for v in variants:
        p = os.path.join(run, "03-spec", "spec-%s.md" % v)
        if os.path.exists(p):
            fm, _ = c.front_matter(p)
            specs[v] = (fm, c.read_text(p))
        else:
            res.add("G2-01", "spec-%s.md 없음" % v)

    # G2-01 배치 방식
    r = g["G2-01"]
    layouts = {}
    for v, (fm, _) in specs.items():
        if fm.get("variant") != v:
            res.add("G2-01", "spec-%s.md variant 값 %s" % (v, fm.get("variant")))
        layouts[v] = fm.get("layout")
        if fm.get("layout") != r["layout"].get(v):
            res.add("G2-01", "spec-%s.md layout '%s' (기준 '%s')" % (v, fm.get("layout"), r["layout"].get(v)))
    if r["must_differ"] and len(layouts) == len(variants) and len(set(layouts.values())) < len(variants):
        res.add("G2-01", "A안과 B안의 layout이 같음")

    for v, (fm, raw) in specs.items():
        sm = screen_map(fm)
        tag = "spec-%s" % v

        # G2-02 화면 포함
        r = g["G2-02"]
        required = list(screens_in) if r["include_all_input_screens"] else []
        required += [s for s in r["required_screens"] if s not in required]
        for s in required:
            if s not in sm:
                res.add("G2-02", "%s: 화면 누락 %s" % (tag, s))
        tt = sm.get("task-tree")
        if tt is not None and len(tt.get("levels") or []) != r["task_tree_levels"]:
            res.add("G2-02", "%s: task-tree 단계 %d개 (기준 %d개)"
                    % (tag, len(tt.get("levels") or []), r["task_tree_levels"]))

        # G2-03 주간 화면 1순위
        r = g["G2-03"]
        if r["screen"] in screens_in and r["screen"] in sm:
            pr = sm[r["screen"]].get("priority") or []
            if not pr or pr[0] != r["priority_1"]:
                res.add("G2-03", "%s: %s 1순위 '%s' (기준 '%s')"
                        % (tag, r["screen"], pr[0] if pr else "", r["priority_1"]))

        # G2-04 계층 용어
        for term in g["G2-04"]["forbidden_terms"]:
            for _ in range(raw.count(term)):
                res.add("G2-04", "%s: 금지 용어 '%s'" % (tag, term))

        # G2-05 계산 근거 일치 (★ 실적 중복 금지)
        r = g["G2-05"]
        per_screen = {}
        for sid, s in sm.items():
            for f in s.get("fields") or []:
                if f.get("name") in r["metric_fields"]:
                    if r["source_id_required"] and not f.get("source_id"):
                        res.add("G2-05", "%s: %s의 '%s'에 source_id 없음" % (tag, sid, f.get("name")))
                    per_screen.setdefault(sid, {}).setdefault(f.get("name"), set()).add(f.get("source_id"))
        across = r["same_metric_same_source_across"]
        if all(s in sm for s in across):
            a, b = across[0], across[1]
            for metric in r["metric_fields"]:
                sa = per_screen.get(a, {}).get(metric)
                sb = per_screen.get(b, {}).get(metric)
                if sa is None or sb is None:
                    res.add("G2-05", "%s: '%s'가 %s/%s 한쪽에 없음" % (tag, metric, a, b))
                elif sa != sb:
                    res.add("G2-05", "%s: '%s' source_id 불일치 %s vs %s"
                            % (tag, metric, sorted(map(str, sa)), sorted(map(str, sb))))
        if r["adjacent_month_label_required"] and "monthly" in sm and "인접 월" not in field_names(sm["monthly"]):
            res.add("G2-05", "%s: monthly에 '인접 월' 표시 항목 없음" % tag)

        # G2-06 삭제 영향 안내 (★ 삭제 시 할 일 보존)
        r = g["G2-06"]
        dc = (fm.get("delete_confirm") or {}).get("fields") or []
        for need in r["delete_confirm_fields"]:
            if need not in dc:
                res.add("G2-06", "%s: delete_confirm에 '%s' 없음" % (tag, need))
        n = sum(1 for s in sm.values() if "미연결" in field_names(s))
        if n < r["unlinked_label_screens_min"]:
            res.add("G2-06", "%s: '미연결' 라벨 화면 %d개 (기준 %d개 이상)"
                    % (tag, n, r["unlinked_label_screens_min"]))
    return res.write(run)


if __name__ == "__main__":
    sys.exit(c.report(check(c.run_dir_arg())))
