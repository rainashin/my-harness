"""게이트 1: 레퍼런스 분석 → 화면 설계. 규칙은 rules.yaml gate1."""
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
import common as c


def check(run):
    rules = c.load_rules()
    g = rules["gate1"]
    res = c.Result("gate1", c.rule_ids(g))
    inp = c.load_json(os.path.join(run, "input.json"))
    screens = inp.get("screens", [])

    ref_path = os.path.join(run, "01-ref-collect", "references.json")
    refs = []
    if os.path.exists(ref_path):
        data = c.load_json(ref_path)
        refs = data.get("references", []) if isinstance(data, dict) else data
    else:
        res.add("G1-01", "references.json 없음")

    # G1-01 개수
    exact = g["G1-01"]["references_exact"]
    if os.path.exists(ref_path) and len(refs) != exact:
        res.add("G1-01", "레퍼런스 %d개 (기준 %d개)" % (len(refs), exact))

    # G1-02 출처와 중복
    dom = g["G1-02"]["url_domain"]
    urls = []
    for r in refs:
        u = str(r.get("url", "")).strip()
        host = (urlparse(u).hostname or "").lower()
        if not (host == dom or host.endswith("." + dom)):
            res.add("G1-02", "%s: 출처가 %s 아님 (%s)" % (r.get("id"), dom, u or "빈 값"))
        urls.append(u.rstrip("/"))
    dup = len(urls) - len(set(urls))
    if dup > g["G1-02"]["duplicate_url_max"]:
        for _ in range(dup):
            res.add("G1-02", "중복 url")

    # G1-03 화면 유형별 최소 개수
    need = g["G1-03"]["per_screen_type_min"]
    for s in screens:
        n = sum(1 for r in refs if r.get("screen_type") == s)
        if n < need:
            res.add("G1-03", "%s 레퍼런스 %d개 (기준 %d개 이상)" % (s, n, need))

    # G1-04 선택 이유
    for r in refs:
        if not str(r.get("reason") or "").strip():
            res.add("G1-04", "%s: reason 비어 있음" % r.get("id"))

    # G1-05 비교표
    rule = g["G1-05"]
    cmp_path = os.path.join(run, "02-ref-analysis", "compare.md")
    if not os.path.exists(cmp_path):
        res.add("G1-05", "compare.md 없음")
    else:
        fm, _ = c.front_matter(cmp_path)
        methods = fm.get("methods") or []
        if len(methods) != rule["methods_exact"]:
            res.add("G1-05", "방식 %d개 (기준 %d개)" % (len(methods), rule["methods_exact"]))
        names = [m.get("name") for m in methods]
        for req in rule["methods"]:
            if req not in names:
                res.add("G1-05", "방식 누락: %s" % req)
        ids = {r.get("id") for r in refs}
        mins = (("pros", rule["pros_min"]), ("cons", rule["cons_min"]), ("refs", rule["evidence_refs_min"]))
        for m in methods:
            nm = m.get("name")
            for key, minimum in mins:
                if len(m.get(key) or []) < minimum:
                    res.add("G1-05", "%s: %s %d개 미만" % (nm, key, minimum))
            for rid in m.get("refs") or []:
                if rid not in ids:
                    res.add("G1-05", "%s: 없는 레퍼런스 id %s" % (nm, rid))

    # G1-06 Figma 프레임
    rule = g["G1-06"]
    fr_path = os.path.join(run, "01-ref-collect", "figma-ref.json")
    if not os.path.exists(fr_path):
        res.add("G1-06", "figma-ref.json 없음")
    else:
        fr = c.load_json(fr_path)
        if fr.get("page") != rule["figma_page"]:
            res.add("G1-06", "페이지 이름 %s (기준 %s)" % (fr.get("page"), rule["figma_page"]))
        n = len(fr.get("frames") or [])
        if n != rule["frames_exact"]:
            res.add("G1-06", "프레임 %d개 (기준 %d개)" % (n, rule["frames_exact"]))
    return res.write(run)


if __name__ == "__main__":
    sys.exit(c.report(check(c.run_dir_arg())))
