"""Phase 4 early-warning CLI.

Usage:
    python -m basr.intel                  # aggregate + detect + alerts
    python -m basr.intel --aggregate      # rebuild time_series only
    python -m basr.intel --detect         # anomaly scan + create alerts
    python -m basr.intel --deliver        # deliver pending alerts
    python -m basr.intel --dry-run        # detect only, no writes
    python -m basr.intel --status 3 dismissed   # lifecycle update
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

from ..store import SupabaseStore
from .aggregate import build_time_series
from .alerts import create_alerts, deliver_alerts, set_alert_status
from .anomaly import detect_anomalies


async def run_intel(*, aggregate: bool, detect: bool, deliver: bool,
                    dry_run: bool = False) -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR early warning (Phase 4)")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   "
          f"dry_run={dry_run} aggregate={aggregate} detect={detect} deliver={deliver}")
    print("=" * 60)

    async with SupabaseStore() as store:
        if aggregate and not dry_run:
            written = await build_time_series(store)
            print(f"[+] time_series: {written} rows upserted")

        if detect:
            anomalies = await detect_anomalies(store)
            print(f"[+] anomalies: {len(anomalies)} flagged "
                  f"({sum(1 for a in anomalies if a['severity'] in ('high', 'critical'))} high+)")
            for a in anomalies:
                print(f"    {a['severity']:8s} {a['dimension_label']:30s} "
                      f"vol={a['volume']:3d} z={a['z']:.2f} stl={a['stl_z']:.2f} "
                      f"score={a['score']:.2f} {a['bucket_start'][:10]}")
            if not dry_run:
                created = await create_alerts(store, anomalies)
                print(f"[+] alerts created: {created}")

        if deliver and not dry_run:
            sent = await deliver_alerts(store)
            print(f"[+] deliveries: {sent} sent")

        print(f"\n[+] Intel finished in {time.monotonic() - t0:.1f}s")
        return 0


async def set_status(alert_id: int, status: str) -> int:
    async with SupabaseStore() as store:
        ok = await set_alert_status(store, alert_id, status)
        print(f"[+] alert {alert_id} -> {status}: {ok}")
        return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="BASR Phase 4 early warning")
    ap.add_argument("--aggregate", action="store_true", help="rebuild time_series")
    ap.add_argument("--detect", action="store_true", help="anomaly scan + create alerts")
    ap.add_argument("--deliver", action="store_true", help="deliver pending alerts")
    ap.add_argument("--dry-run", action="store_true", help="detect only, no writes")
    ap.add_argument("--status", nargs=2, metavar=("ID", "STATUS"),
                    help="lifecycle: acknowledged|dismissed|promoted")
    args = ap.parse_args()

    if args.status:
        raise SystemExit(asyncio.run(set_status(int(args.status[0]), args.status[1])))
    do_all = not (args.aggregate or args.detect or args.deliver)
    raise SystemExit(asyncio.run(run_intel(
        aggregate=args.aggregate or do_all,
        detect=args.detect or do_all,
        deliver=args.deliver or do_all,
        dry_run=args.dry_run,
    )))


if __name__ == "__main__":
    main()
