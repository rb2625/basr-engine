"""Phase 5 agents CLI (A12).

Usage:
    python -m basr.agents --brief <alert_id> [--publish]   # brief for an alert
    python -m basr.agents --report daily|weekly            # scheduled report
    python -m basr.agents --deliver                        # deliver pending reports
    python -m basr.agents --status <brief_id> published    # lifecycle update
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

from ..store import SupabaseStore
from .brief import build_brief
from .reports import build_report, deliver_reports


async def run_agents(*, brief_id: int | None = None, publish: bool = False,
                     report: str | None = None, deliver: bool = False,
                     dry_run: bool = False) -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR agents (Phase 5)")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   "
          f"brief={brief_id} report={report} deliver={deliver} "
          f"dry_run={dry_run}")
    print("=" * 60)

    async with SupabaseStore() as store:
        if brief_id is not None:
            rec = await build_brief(store, brief_id, publish=publish)
            if rec is None:
                return 1
        if report:
            row = await build_report(store, report, dry_run=dry_run)
            if row is None:
                return 1
        if deliver and not dry_run:
            sent = await deliver_reports(store)
            print(f"[+] reports delivered: {sent}")

        print(f"\n[+] Agents finished in {time.monotonic() - t0:.1f}s")
        return 0


async def set_status(brief_id: int, status: str) -> int:
    async with SupabaseStore() as store:
        try:
            await store._with_retry(
                lambda: store._client.table("briefs")
                .update({"status": status}).eq("id", brief_id).execute())
            print(f"[+] brief {brief_id} -> {status}")
            return 0
        except Exception as exc:
            print(f"    [-] status update failed: {str(exc)[:120]}")
            return 1


def main() -> None:
    ap = argparse.ArgumentParser(description="BASR Phase 5 agents")
    ap.add_argument("--brief", type=int, metavar="ALERT_ID",
                    help="build a brief for an alert")
    ap.add_argument("--publish", action="store_true",
                    help="write the brief as published (default draft)")
    ap.add_argument("--report", choices=("daily", "weekly"),
                    help="build a scheduled report")
    ap.add_argument("--deliver", action="store_true",
                    help="deliver pending reports")
    ap.add_argument("--dry-run", action="store_true",
                    help="compute only, no DB writes or delivery")
    ap.add_argument("--status", nargs=2, metavar=("BRIEF_ID", "STATUS"),
                    help="brief lifecycle: draft|published|delivered|archived")
    args = ap.parse_args()

    if args.status:
        raise SystemExit(asyncio.run(set_status(int(args.status[0]),
                                                args.status[1])))
    if not (args.brief or args.report or args.deliver):
        ap.print_help()
        raise SystemExit(2)
    raise SystemExit(asyncio.run(run_agents(
        brief_id=args.brief, publish=args.publish,
        report=args.report, deliver=args.deliver, dry_run=args.dry_run,
    )))


if __name__ == "__main__":
    main()
