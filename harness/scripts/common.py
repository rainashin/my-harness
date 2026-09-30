"""판정 스크립트 공용 로더. 숫자 규칙은 rules.yaml, 토큰은 design.md 앞머리에서만 읽는다."""
import datetime
import io
import json
import os
import re
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RULES_PATH = os.path.join(ROOT, "harness", "rules", "rules.yaml")

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def load_yaml(path):
    return yaml.safe_load(read_text(path))


def load_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def load_rules():
    return load_yaml(RULES_PATH)


def front_matter(path):
    """마크다운 앞머리(YAML)와 본문을 돌려준다. 앞머리가 없으면 ({}, 본문)."""
    text = read_text(path).lstrip("\ufeff")
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)(.*)$", text, re.S)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


def numbers(value):
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", str(value))]


def norm_hex(value):
    if value is None:
        return None
    v = str(value).strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", v):
        v = "#" + "".join(c * 2 for c in v[1:])
    return v[:7] if re.fullmatch(r"#[0-9a-f]{6}([0-9a-f]{2})?", v) else v


def load_tokens(rules):
    """design.md 앞머리에서 허용 토큰 집합을 만든다.

    간격 허용값 = spacing 토큰 + design.md 컴포넌트에 적힌 padding 값 + 0(간격 없음).
    """
    t = rules["tokens"]
    fm, _ = front_matter(os.path.join(ROOT, t["source"]))
    radius = {n for v in fm[t["radius_from"]].values() for n in numbers(v)}
    spacing = {n for v in fm[t["spacing_from"]].values() for n in numbers(v)}
    for comp in (fm.get("components") or {}).values():
        if isinstance(comp, dict) and "padding" in comp:
            spacing.update(numbers(comp["padding"]))
    spacing.add(0.0)
    typo_key = t["font_size_from"].split(".")[0]
    font = {n for v in fm[typo_key].values() for n in numbers(v.get("fontSize"))}
    colors = {norm_hex(v) for v in fm[t["colors_from"]].values()}
    return {"radius": radius, "spacing": spacing, "font_size": font, "colors": colors}


def rule_ids(section):
    return [k for k in section if re.fullmatch(r"[A-Z0-9]+-\d+", str(k))]


class Result:
    def __init__(self, name, ids):
        self.name = name
        self.violations = {i: 0 for i in ids}
        self.items = []

    def add(self, rule, detail, **extra):
        self.violations[rule] = self.violations.get(rule, 0) + 1
        item = {"rule": rule, "detail": detail}
        item.update(extra)
        self.items.append(item)

    def write(self, run_dir, max_violations=0):
        state_path = os.path.join(run_dir, "state.json")
        attempt = 1
        if os.path.exists(state_path):
            try:
                attempt = int(load_json(state_path).get("fail_count", {}).get(self.name, 0)) + 1
            except Exception:
                attempt = 1
        total = sum(self.violations.values())
        out = {
            "gate": self.name,
            "passed": total <= max_violations,
            "date": datetime.datetime.now().isoformat(timespec="seconds"),
            "attempt": attempt,
            "violations": self.violations,
            "total": total,
            "items": self.items,
        }
        os.makedirs(os.path.join(run_dir, "gates"), exist_ok=True)
        with io.open(os.path.join(run_dir, "gates", self.name + ".json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return out


def report(out):
    print("[%s] %s  위반 %d개" % (out["gate"], "PASS" if out["passed"] else "FAIL", out["total"]))
    for rid, n in out["violations"].items():
        if n:
            print("  %s: %d" % (rid, n))
    for it in out["items"]:
        print("   - %s %s" % (it["rule"], it["detail"]))
    return 0 if out["passed"] else 1


def run_dir_arg():
    if len(sys.argv) < 2:
        sys.exit("사용법: python %s <실행 폴더>" % os.path.basename(sys.argv[0]))
    return os.path.abspath(sys.argv[1])
