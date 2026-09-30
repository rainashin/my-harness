"""판정 스크립트 검증. 예시마다 걸린 규칙 ID 집합이 expected.json과 같아야 한다.

사용법: python harness/tests/run_tests.py
예시는 임시 폴더에 복사해서 돌린다. fixtures 폴더에는 판정 결과를 쓰지 않는다.
"""
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import check_gate1  # noqa: E402
import check_gate2  # noqa: E402
import check_guide  # noqa: E402

CHECKERS = {"gate1": check_gate1.check, "gate2": check_gate2.check, "guide": check_guide.check}
FIX = os.path.join(HERE, "fixtures")


def main():
    rows, mismatches = [], 0
    for suite in sorted(os.listdir(FIX)):
        for case in sorted(os.listdir(os.path.join(FIX, suite))):
            src = os.path.join(FIX, suite, case)
            with io.open(os.path.join(src, "expected.json"), encoding="utf-8") as f:
                expected = set(json.load(f)["violated"])
            tmp = tempfile.mkdtemp()
            try:
                run = os.path.join(tmp, "run")
                shutil.copytree(src, run)
                out = CHECKERS[suite](run)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            got = {k for k, v in out["violations"].items() if v}
            ok = got == expected and out["passed"] == (not expected)
            mismatches += 0 if ok else 1
            rows.append((suite, case, sorted(expected), sorted(got), ok))

    for suite, case, exp, got, ok in rows:
        print("%-5s %-6s %-6s expected=%s got=%s" % ("OK" if ok else "FAIL", suite, case, exp, got))
    print("\n예시 %d개, 불일치 %d개" % (len(rows), mismatches))
    return 1 if mismatches else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
