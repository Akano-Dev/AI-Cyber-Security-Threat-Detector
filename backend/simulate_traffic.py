"""
ACSTD synthetic traffic simulator (CLI entrypoint).

Generates synthetic demo traffic against the detector's /api/v1/analyze
endpoint. Payloads are textbook detection-test strings, not real exploits.

Backwards compatible: running it with no arguments behaves like before —
an endless ~mostly-benign mixed stream that lights up the dashboard.

Examples:
    python simulate_traffic.py                       # endless mixed stream (default)
    python simulate_traffic.py --scenario sqli --count 5
    python simulate_traffic.py --scenario rate_abuse --burst 40
    python simulate_traffic.py --scenario port_scan --ports 12
    python simulate_traffic.py --dry-run --count 10  # generate + print, don't send

Reusable building blocks live in the `simulator/` package:
    from simulator import AnalyzeClient, Simulator, SCENARIOS
"""
import argparse
import random
import time

from simulator import AnalyzeClient, Simulator, SCENARIOS


def main():
    ap = argparse.ArgumentParser(description="ACSTD synthetic traffic simulator")
    ap.add_argument("--scenario", choices=["mixed", *SCENARIOS], default="mixed",
                    help="traffic profile to run (default: mixed)")
    ap.add_argument("--url", default="http://localhost:8000/api/v1",
                    help="ACSTD API base URL")
    ap.add_argument("--count", type=int, default=None,
                    help="number of scenarios to run (default: infinite for mixed, 1 otherwise)")
    ap.add_argument("--burst", type=int, default=30, help="requests per rate-abuse burst")
    ap.add_argument("--ports", type=int, default=12, help="probes per port scan")
    ap.add_argument("--min-delay", type=float, default=1.0, help="min seconds between scenarios")
    ap.add_argument("--max-delay", type=float, default=2.0, help="max seconds between scenarios")
    ap.add_argument("--dry-run", action="store_true", help="generate + print without sending")
    args = ap.parse_args()

    client = AnalyzeClient(args.url)
    sim = Simulator(client, delay=(args.min_delay, args.max_delay), dry_run=args.dry_run)

    mode = "DRY-RUN" if args.dry_run else f"-> {args.url}"
    print(f"Traffic simulator [{args.scenario}] {mode} - Ctrl+C to stop.\n")

    try:
        if args.scenario == "mixed":
            sim.run_mixed(count=args.count)
        else:
            kwargs = {}
            if args.scenario == "rate_abuse":
                kwargs["burst"] = args.burst
            elif args.scenario == "port_scan":
                kwargs["ports"] = args.ports
            for _ in range(args.count or 1):
                sim.run_scenario(args.scenario, **kwargs)
                time.sleep(random.uniform(args.min_delay, args.max_delay))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
