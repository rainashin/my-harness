"""디자인 제작 완료 조건(가이드 검토). 규칙은 rules.yaml guide, 토큰은 design.md."""
import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import common as c


def rgb(hexv):
    h = hexv.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def luminance(hexv):
    def ch(x):
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb(hexv))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hsl(hexv):
    h, l, s = colorsys.rgb_to_hls(*rgb(hexv))
    return h * 360, s * 100, l * 100


def paint(n):
    return [c.norm_hex(x) for x in (n.get("fills") or []) + (n.get("strokes") or []) if x]


def node_colors(n):
    cols = paint(n)
    if n.get("textColor"):
        cols.append(c.norm_hex(n["textColor"]))
    return cols


def is_text(n):
    return str(n.get("type", "")).upper() == "TEXT"


def check(run):
    rules = c.load_rules()
    g = rules["guide"]
    tok = c.load_tokens(rules)
    res = c.Result("guide", c.rule_ids(g))
    lav = {c.norm_hex(x) for x in g["D-07"]["colors"]}
    done_color = c.norm_hex(g["D-06"]["completed_color"])

    for v in rules["run"]["variants"]:
        p = os.path.join(run, "04-design", "nodes-%s.json" % v)
        if not os.path.exists(p):
            res.add("D-01", "nodes-%s.json 없음" % v, variant=v)
            continue
        data = c.load_json(p)
        nodes = data.get("nodes") or []
        frames = {f["id"]: f for f in data.get("frames") or []}

        def add(rule, n, detail):
            res.add(rule, "%s %s(%s): %s" % (v, n.get("id"), n.get("name"), detail),
                    variant=v, node=n.get("id"))

        cat_colors = set()
        cat_area = {}
        for n in nodes:
            name = str(n.get("name", ""))
            lname = name.lower()
            is_cat = name.startswith("cat/")

            # D-01 토큰 값
            if n.get("cornerRadius") is not None and float(n["cornerRadius"]) not in tok["radius"]:
                add("D-01", n, "모서리 %s" % n["cornerRadius"])
            if n.get("itemSpacing") is not None and float(n["itemSpacing"]) not in tok["spacing"]:
                add("D-01", n, "간격 %s" % n["itemSpacing"])
            for pad in n.get("padding") or []:
                if float(pad) not in tok["spacing"]:
                    add("D-01", n, "패딩 %s" % pad)
            if n.get("fontSize") is not None and float(n["fontSize"]) not in tok["font_size"]:
                add("D-01", n, "글자 크기 %s" % n["fontSize"])

            cols = node_colors(n)
            if not is_cat:
                # D-02 기본 색
                for col in cols:
                    if col not in tok["colors"]:
                        add("D-02", n, "design.md에 없는 색 %s" % col)
            else:
                cat_colors.update(c.norm_hex(x) for x in n.get("fills") or [])
                # D-04 분류색 요소 높이
                if float(n.get("height") or 0) > g["D-04"]["max_node_height_px"]:
                    add("D-04", n, "분류색 요소 높이 %s" % n.get("height"))
                fr = n.get("frame")
                cat_area[fr] = cat_area.get(fr, 0.0) + float(n.get("width") or 0) * float(n.get("height") or 0)

            # D-05 명암비
            if is_text(n) and n.get("textColor") and n.get("bg"):
                ratio = contrast(c.norm_hex(n["textColor"]), c.norm_hex(n["bg"]))
                if ratio < g["D-05"]["min_contrast"]:
                    add("D-05", n, "명암비 %.2f" % ratio)

            # D-06 완료 표시
            if "completed" in lname:
                if is_text(n):
                    if "text" in g["D-06"]["applies_to"] and c.norm_hex(n.get("textColor")) != done_color:
                        add("D-06", n, "완료 글자색 %s" % n.get("textColor"))
                elif "checkbox" in g["D-06"]["applies_to"] and done_color not in paint(n):
                    add("D-06", n, "완료 체크박스에 %s 없음" % done_color)

            # D-07 라벤더 전용
            if lav.intersection(cols) and not any(k in lname for k in g["D-07"]["allowed_node_name_contains"]):
                add("D-07", n, "라벤더 사용")

            # D-08 삭제 문구 금지어 (★ 삭제 시 할 일 보존)
            if is_text(n):
                for ph in g["D-08"]["forbidden_phrases"]:
                    if ph in str(n.get("characters", "")):
                        add("D-08", n, "금지어 '%s'" % ph)

        # D-03 분류색
        r = g["D-03"]
        if len(cat_colors) > r["max_count"]:
            res.add("D-03", "%s: 분류색 %d개 (기준 %d개 이하)" % (v, len(cat_colors), r["max_count"]), variant=v)
        cl = sorted(cat_colors)
        for i, a in enumerate(cl):
            ha, sa, la = hsl(a)
            if sa > r["hsl_saturation_max"] or not (r["hsl_lightness_min"] <= la <= r["hsl_lightness_max"]):
                res.add("D-03", "%s: %s 채도 %.0f 명도 %.0f" % (v, a, sa, la), variant=v)
            for b in cl[i + 1:]:
                gap = abs(ha - hsl(b)[0])
                gap = min(gap, 360 - gap)
                if gap < r["min_hue_gap_deg"]:
                    res.add("D-03", "%s: %s와 %s 색상각 %.0f도" % (v, a, b, gap), variant=v)

        # D-04 분류색 면적
        for fid, area in cat_area.items():
            f = frames.get(fid)
            if not f:
                res.add("D-04", "%s: 분류색 노드의 frame %s가 frames에 없음" % (v, fid), variant=v)
                continue
            ratio = area / (float(f["width"]) * float(f["height"]))
            if ratio > g["D-04"]["max_area_ratio"]:
                res.add("D-04", "%s: 프레임 %s 분류색 면적 %.1f%%" % (v, fid, ratio * 100), variant=v)
    return res.write(run, g["violations_max"])


if __name__ == "__main__":
    sys.exit(c.report(check(c.run_dir_arg())))
