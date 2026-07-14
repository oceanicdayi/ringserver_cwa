#!/usr/bin/env python3
"""Subscribe to earthquake event JSON packets from ringserver via DataLink."""

from __future__ import annotations

import argparse
import json
import sys

from ringserver_client import DEFAULT_MATCH, subscribe_events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=16000)
    parser.add_argument("--match", default=DEFAULT_MATCH)
    parser.add_argument(
        "--from-earliest",
        action="store_true",
        help="Replay from earliest buffered packet instead of latest",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Stop after N packets (0 = keep collecting until interrupted)",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    # CLI continuous mode: large count when 0, user interrupts with Ctrl-C.
    count = args.count if args.count > 0 else 10_000_000
    print(f"streaming match={args.match!r} from {args.host}:{args.port}", flush=True)

    result = subscribe_events(
        host=args.host,
        port=args.port,
        match=args.match,
        count=count,
        from_earliest=args.from_earliest,
        timeout=args.timeout if args.count > 0 else max(args.timeout, 3600.0),
    )

    for item in result.get("events", []):
        print("---")
        print(f"stream_id={item.get('stream_id')}")
        print(f"pktid={item.get('pktid')}")
        if "event" in item:
            print(json.dumps(item["event"], ensure_ascii=False, indent=2), flush=True)
        else:
            print(item, flush=True)

    if result.get("error"):
        print(f"error: {result['error']}", file=sys.stderr)
        return 1
    if result.get("note") and not result.get("events"):
        print(result["note"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nstopped", file=sys.stderr)
        raise SystemExit(0)
