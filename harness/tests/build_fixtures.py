"""판정 스크립트 검증용 예시(fixture)를 만든다.

스크립트마다 통과 예시 1개(pass)와 규칙별 실패 예시를 만든다. 실패 예시는 통과 예시에서
규칙 하나만 어기도록 바꾼 것이다. expected.json에 걸려야 하는 규칙 ID를 적는다.
사용법: python harness/tests/build_fixtures.py
"""
import colorsys
import copy
import io
import json
import os
import shutil

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fixtures")


def hsl_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return "#%02x%02x%02x" % tuple(round(x * 255) for x in (r, g, b))


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_md(path, fm, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n" + body)


INPUT = {"prd_version": "fixture", "screens": ["weekly", "monthly"], "figma_file_key": "FIXTURE",
         "pages": {"00_Gate Log": "0:1", "01_Reference": "0:2", "02_Screen Spec": "0:3", "03_Design": "0:4"}}


# ---------- gate1 ----------
def gate1_base():
    types = ["weekly"] * 4 + ["monthly"] * 3 + ["task-tree"] * 3
    refs = [{"id": "R%02d" % (i + 1), "url": "https://uibowl.io/screens/%d" % (1001 + i),
             "screen_type": t, "reason": "%s 화면의 정보 배치 참고" % t} for i, t in enumerate(types)]
    methods = [
        {"name": "주간 7일 배치", "pros": ["한 주 전체가 보인다"], "cons": ["하루 상세가 좁다"], "refs": ["R01"]},
        {"name": "오늘 할 일 강조", "pros": ["오늘 미완료가 먼저 보인다"], "cons": ["주간 맥락이 약하다"], "refs": ["R02"]},
        {"name": "태스크 단위 보기", "pros": ["월·주·일 연결이 보인다"], "cons": ["날짜 감각이 약하다"], "refs": ["R08"]},
        {"name": "월간 보기", "pros": ["영역별 지연이 보인다"], "cons": ["밀도가 높다"], "refs": ["R05"]},
    ]
    return {
        "refs": refs,
        "frames": [{"id": "10:%d" % i, "name": r["id"]} for i, r in enumerate(refs)],
        "methods": methods,
    }


def gate1_write(d, data):
    write_json(os.path.join(d, "input.json"), INPUT)
    write_json(os.path.join(d, "01-ref-collect", "references.json"), {"references": data["refs"]})
    write_json(os.path.join(d, "01-ref-collect", "figma-ref.json"), {"page": "01_Reference", "frames": data["frames"]})
    write_md(os.path.join(d, "02-ref-analysis", "compare.md"), {"methods": data["methods"]}, "# 표현 방식 비교\n")


def gate1_cases():
    b = gate1_base()
    cases = {"pass": (b, [])}

    x = copy.deepcopy(b); x["refs"] = x["refs"][:9]
    cases["G1-01"] = (x, ["G1-01"])
    x = copy.deepcopy(b); x["refs"][1]["url"] = "https://www.pinterest.com/pin/1"
    cases["G1-02"] = (x, ["G1-02"])
    x = copy.deepcopy(b); x["refs"][5]["screen_type"] = "task-tree"; x["refs"][6]["screen_type"] = "task-tree"
    cases["G1-03"] = (x, ["G1-03"])
    x = copy.deepcopy(b); x["refs"][2]["reason"] = ""
    cases["G1-04"] = (x, ["G1-04"])
    x = copy.deepcopy(b); x["methods"] = x["methods"][:3]
    cases["G1-05"] = (x, ["G1-05"])
    x = copy.deepcopy(b); x["frames"] = x["frames"][:9]
    cases["G1-06"] = (x, ["G1-06"])
    return cases


# ---------- gate2 ----------
def spec_base(variant, layout):
    metrics = [{"name": "진행률", "source_id": "SRC-progress"},
               {"name": "완료량", "source_id": "SRC-done"},
               {"name": "남은 양", "source_id": "SRC-remain"}]
    fm = {
        "variant": variant,
        "layout": layout,
        "screens": [
            {"id": "weekly", "priority": ["오늘의 미완료 할 일", "주차별 목표 진행률", "이번 주 할 일"],
             "fields": [{"name": "오늘의 미완료 할 일"}] + copy.deepcopy(metrics) + [{"name": "미연결"}]},
            {"id": "monthly", "priority": ["목표 영역별 진행률", "주차별 계획량"],
             "fields": copy.deepcopy(metrics) + [{"name": "인접 월"}]},
            {"id": "task-tree", "levels": ["월 태스크", "주 태스크", "일 태스크"],
             "priority": ["월 목표", "주차별 목표", "일간 할 일"],
             "fields": [{"name": "월 목표"}, {"name": "주차별 목표"}, {"name": "일간 할 일"}]},
        ],
        "delete_confirm": {"fields": ["affected_tasks_count", "미연결로 보존"]},
    }
    body = "# 화면 설계 %s안\n\n목표 영역, 월 목표, 주차별 목표, 일간 할 일을 태스크 단위로 묶어 본다.\n" % variant
    return {"fm": fm, "body": body}


def gate2_base():
    return {"A": spec_base("A", "7일 열 배치"), "B": spec_base("B", "하루 상세 + 주간 요약")}


def gate2_write(d, data):
    write_json(os.path.join(d, "input.json"), INPUT)
    for v, s in data.items():
        write_md(os.path.join(d, "03-spec", "spec-%s.md" % v), s["fm"], s["body"])


def gate2_cases():
    b = gate2_base()
    cases = {"pass": (b, [])}

    x = copy.deepcopy(b); x["B"]["fm"]["layout"] = "7일 열 배치"
    cases["G2-01"] = (x, ["G2-01"])
    x = copy.deepcopy(b); x["A"]["fm"]["screens"] = [s for s in x["A"]["fm"]["screens"] if s["id"] != "task-tree"]
    cases["G2-02"] = (x, ["G2-02"])
    x = copy.deepcopy(b); x["A"]["fm"]["screens"][0]["priority"] = ["주차별 목표 진행률", "오늘의 미완료 할 일"]
    cases["G2-03"] = (x, ["G2-03"])
    x = copy.deepcopy(b); x["A"]["body"] += "\n월 목표를 에픽처럼 묶는다.\n"
    cases["G2-04"] = (x, ["G2-04"])
    x = copy.deepcopy(b); del x["A"]["fm"]["screens"][0]["fields"][1]["source_id"]
    cases["G2-05"] = (x, ["G2-05"])
    x = copy.deepcopy(b); x["A"]["fm"]["delete_confirm"]["fields"] = ["affected_tasks_count"]
    cases["G2-06"] = (x, ["G2-06"])
    return cases


# ---------- guide ----------
CAT1 = hsl_hex(210, 55, 55)
CAT2 = hsl_hex(30, 55, 55)


def nodes_base(variant):
    F = "1:1"
    nodes = [
        {"id": "1:1", "name": "weekly", "type": "FRAME", "frame": F, "width": 1440, "height": 1024, "fills": ["#010102"]},
        {"id": "1:2", "name": "card/today", "type": "FRAME", "frame": F, "width": 600, "height": 400,
         "fills": ["#0f1011"], "strokes": ["#23252a"], "cornerRadius": 12, "padding": [24, 24, 24, 24], "itemSpacing": 16},
        {"id": "1:3", "name": "title", "type": "TEXT", "frame": F, "width": 200, "height": 28,
         "textColor": "#f7f8f8", "bg": "#0f1011", "fontSize": 22, "characters": "오늘 할 일"},
        {"id": "1:4", "name": "task", "type": "TEXT", "frame": F, "width": 300, "height": 20,
         "textColor": "#f7f8f8", "bg": "#0f1011", "fontSize": 14, "characters": "스레드 1개 작성"},
        {"id": "1:5", "name": "task-completed", "type": "TEXT", "frame": F, "width": 300, "height": 20,
         "textColor": "#8a8f98", "bg": "#0f1011", "fontSize": 14, "characters": "주제 3개 선정"},
        {"id": "1:6", "name": "checkbox-completed", "type": "RECTANGLE", "frame": F, "width": 16, "height": 16,
         "fills": ["#8a8f98"], "cornerRadius": 4},
        {"id": "1:7", "name": "cat/sns", "type": "ELLIPSE", "frame": F, "width": 8, "height": 8, "fills": [CAT1]},
        {"id": "1:8", "name": "cat/study", "type": "ELLIPSE", "frame": F, "width": 8, "height": 8, "fills": [CAT2]},
        {"id": "1:9", "name": "button-primary", "type": "FRAME", "frame": F, "width": 96, "height": 32,
         "fills": ["#5e6ad2"], "cornerRadius": 8, "padding": [8, 14, 8, 14]},
        {"id": "1:10", "name": "button-primary/label", "type": "TEXT", "frame": F, "width": 60, "height": 17,
         "textColor": "#ffffff", "bg": "#5e6ad2", "fontSize": 14, "characters": "할 일 추가"},
        {"id": "1:11", "name": "delete-confirm", "type": "TEXT", "frame": F, "width": 360, "height": 20,
         "textColor": "#d0d6e0", "bg": "#141516", "fontSize": 14,
         "characters": "목표를 삭제해도 할 일 3개는 미연결로 보존돼요"},
    ]
    return {"variant": variant, "frames": [{"id": F, "name": "weekly", "width": 1440, "height": 1024}], "nodes": nodes}


def guide_base():
    return {"A": nodes_base("A"), "B": nodes_base("B")}


def guide_write(d, data):
    write_json(os.path.join(d, "input.json"), INPUT)
    for v, n in data.items():
        write_json(os.path.join(d, "04-design", "nodes-%s.json" % v), n)


def node(x, nid):
    return next(n for n in x["A"]["nodes"] if n["id"] == nid)


def guide_cases():
    b = guide_base()
    cases = {"pass": (b, [])}

    x = copy.deepcopy(b); node(x, "1:2")["cornerRadius"] = 10
    cases["D-01"] = (x, ["D-01"])
    x = copy.deepcopy(b); node(x, "1:2")["fills"] = ["#123456"]
    cases["D-02"] = (x, ["D-02"])
    x = copy.deepcopy(b); node(x, "1:8")["fills"] = [hsl_hex(220, 55, 55)]
    cases["D-03"] = (x, ["D-03"])
    x = copy.deepcopy(b); node(x, "1:7")["height"] = 40
    cases["D-04"] = (x, ["D-04"])
    x = copy.deepcopy(b); node(x, "1:4").update({"textColor": "#62666d", "bg": "#010102"})
    cases["D-05"] = (x, ["D-05"])
    x = copy.deepcopy(b); node(x, "1:5")["textColor"] = "#d0d6e0"
    cases["D-06"] = (x, ["D-06"])
    x = copy.deepcopy(b); node(x, "1:2")["fills"] = ["#5e6ad2"]
    cases["D-07"] = (x, ["D-07"])
    x = copy.deepcopy(b); node(x, "1:11")["characters"] = "목표와 함께 삭제됩니다"
    cases["D-08"] = (x, ["D-08"])
    return cases


SUITES = {
    "gate1": (gate1_cases, gate1_write),
    "gate2": (gate2_cases, gate2_write),
    "guide": (guide_cases, guide_write),
}


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    total = 0
    for suite, (cases_fn, write_fn) in SUITES.items():
        for name, (data, expected) in cases_fn().items():
            d = os.path.join(OUT, suite, name)
            write_fn(d, data)
            write_json(os.path.join(d, "expected.json"), {"suite": suite, "violated": expected})
            total += 1
    print("fixtures: %d" % total)


if __name__ == "__main__":
    main()
