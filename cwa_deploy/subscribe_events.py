#!/usr/bin/env python3
"""Subscribe to earthquake event JSON packets from ringserver via DataLink."""

from __future__ import annotations

import argparse
import json
import sys

from datalink_client import DataLink


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=16000)
    parser.add_argument(
        "--match",
        default=".*/JSON",
        help="DataLink stream ID regex (default: .*/JSON)",
    )
    parser.add_argument(
        "--from-earliest",
        action="store_true",
        help="Replay from earliest buffered packet instead of latest",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Stop after N packets (0 = run forever)",
    )
    args = parser.parse_args()

    received = 0
    with DataLink(args.host, args.port) as dl:
        dl.identify("subscribe_events")
        dl.match(args.match)
        if args.from_earliest:
            dl.position_set("EARLIEST")
        else:
            dl.set_position_latest()

        print(f"streaming match={args.match!r} from {args.host}:{args.port}", flush=True)
        dl.stream()

        for packet in dl.collect():
            try:
                text = packet.data.decode("utf-8")
                event = json.loads(text)
                pretty = json.dumps(event, ensure_ascii=False, indent=2)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                pretty = f"<non-json payload: {exc}> bytes={len(packet.data)}"

            print("---")
            print(f"stream_id={packet.streamid}")
            print(f"pktid={packet.pktid}")
            print(pretty, flush=True)

            received += 1
            if args.count and received >= args.count:
                break

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nstopped", file=sys.stderr)
        raise SystemExit(0)
