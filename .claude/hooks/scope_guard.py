"""PreToolUse 훅: 에이전트별 편집 범위를 강제한다. 범위는 harness/rules/rules.yaml scope.

- 하네스 에이전트(scope에 이름이 있는 서브에이전트): harness/runs/<실행ID>/<자기 폴더> 안에만 쓸 수 있다.
- 메인 세션과 그 밖의 에이전트: 실행 폴더 안에서는 scope.main에 적힌 파일만 쓸 수 있다.
  실행 폴더 밖(harness 문서 등)은 막지 않는다.
- 막으면 종료 코드 2로 이유를 알리고 실행 폴더의 blocked.log에 한 줄 남긴다.
- 훅 입력에 어떤 키가 오는지 harness/runs/.hook-input-keys.json에 남긴다(서브에이전트 이름 확인용).
"""
import datetime
import io
import json
import os
import sys

try:
    import yaml
except ImportError:  # 규칙을 못 읽으면 막지 않고 알린다
    yaml = None


def err(msg):
    sys.stderr.buffer.write((msg + "\n").encode("utf-8"))
    sys.stderr.flush()


def main():
    raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    try:
        data = json.loads(raw)
    except Exception:
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    root = os.path.abspath(root)
    runs = os.path.join(root, "harness", "runs")

    agent = data.get("agent_type") or data.get("agent_name") or data.get("subagent_type") or "main"
    try:
        os.makedirs(runs, exist_ok=True)
        with io.open(os.path.join(runs, ".hook-input-keys.json"), "w", encoding="utf-8") as f:
            json.dump({"keys": sorted(data.keys()), "agent_seen": agent,
                       "time": datetime.datetime.now().isoformat(timespec="seconds")}, f, ensure_ascii=False)
    except Exception:
        pass

    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path")
    if not path:
        return 0
    path = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))

    if yaml is None:
        err("scope_guard: PyYAML 없음. 범위 검사를 건너뜀")
        return 0
    with io.open(os.path.join(root, "harness", "rules", "rules.yaml"), encoding="utf-8") as f:
        scope = (yaml.safe_load(f) or {}).get("scope") or {}

    def norm(p):
        return os.path.normcase(os.path.normpath(p))

    in_runs = norm(path).startswith(norm(runs) + os.sep)
    rel = os.path.relpath(path, runs).replace("\\", "/") if in_runs else None
    run_id, inner = (rel.split("/", 1) + [""])[:2] if rel else (None, None)

    def allowed(entries):
        return any(inner == e or (e.endswith("/") and inner.startswith(e)) for e in entries)

    if agent in scope and agent != "main":
        ok = bool(run_id) and allowed(scope[agent])
    else:
        ok = (not in_runs) or (not inner) or allowed(scope.get("main", []))

    if ok:
        return 0

    reason = "scope_guard: %s는 %s에 쓸 수 없음 (허용: %s)" % (
        agent, (rel or path), ", ".join(scope.get(agent if agent in scope else "main", [])) or "없음")
    try:
        log_dir = os.path.join(runs, run_id) if run_id and os.path.isdir(os.path.join(runs, run_id)) else runs
        with io.open(os.path.join(log_dir, "blocked.log"), "a", encoding="utf-8") as f:
            f.write("%s\t%s\t%s\t%s\n" % (datetime.datetime.now().isoformat(timespec="seconds"),
                                          agent, data.get("tool_name"), rel or path))
    except Exception:
        pass
    err(reason)
    return 2


if __name__ == "__main__":
    sys.exit(main())
