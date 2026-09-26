#!/usr/bin/env python3
"""Explicit reading_chunks additive maintenance. Default is a READ ONLY plan."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.schema_maintenance import plan_reading_chunks, apply_reading_chunks
from tools.schema_preflight import target_arguments, connect_target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target_arguments(parser)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approve-plan", help="사용자가 검토/승인한 plan_sha256. 승인 자체를 대체하지 않음")
    args = parser.parse_args()
    if args.apply != bool(args.approve_plan):
        parser.error("실행은 --apply와 --approve-plan을 함께 명시해야 합니다.")
    try:
        conn = connect_target(args, readonly=not args.apply)
        try:
            plan = apply_reading_chunks(conn, approved_plan_sha256=args.approve_plan) if args.apply else plan_reading_chunks(conn)
        finally:
            conn.close()
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0 if plan["applicable"] else 2
    except Exception:
        print(json.dumps(dict(status="UNKNOWN_ERROR", detail="관리 작업 중단. 승인 범위/구조/권한을 확인하세요. 자동 재시도하지 않습니다."), ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main())
