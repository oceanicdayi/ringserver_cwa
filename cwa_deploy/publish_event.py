#!/usr/bin/env python3
"""Publish one earthquake event JSON packet to ringserver via DataLink."""

from __future__ import annotations

import argparse
import json
import sys

from ringserver_client import DEFAULT_STREAM_ID, build_demo_event, publish_event


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=16000)
    parser.add_argument("--stream-id", default=DEFAULT_STREAM_ID)
    parser.add_argument("--event-id", default=None)
    parser.add_argument(
        "--payload",
        default=None,
        help="Path to a JSON file to publish instead of the demo event",
    )
    args = parser.parse_args()

    if args.payload:
        with open(args.payload, encoding="utf-8") as f:
            event = json.load(f)
    else:
        event = build_demo_event(args.event_id)

    result = publish_event(args.host, args.port, args.stream_id, event)
    print(
        f"published stream_id={result['stream_id']} "
        f"bytes={result['bytes']} pktid={result['pktid']}"
    )
    print(json.dumps(result["event"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
