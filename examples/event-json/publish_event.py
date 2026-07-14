#!/usr/bin/env python3
"""Publish one earthquake event JSON packet to ringserver via DataLink."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone

from datalink_client import DataLink


DEFAULT_STREAM_ID = "TW_DEMO_EVENT/JSON"


def build_event(event_id: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "type": "earthquake",
        "version": 1,
        "event_id": event_id or f"demo-{uuid.uuid4().hex[:12]}",
        "origin_time": now.isoformat().replace("+00:00", "Z"),
        "latitude": 23.9,
        "longitude": 121.6,
        "depth_km": 10.0,
        "magnitude": 5.2,
        "magnitude_type": "ML",
        "region": "Hualien area",
        "status": "preliminary",
        "source": "demo-publisher",
    }


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
        event = build_event(args.event_id)

    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # DataLink times are integer microseconds since Unix epoch.
    t_us = int(time.time() * 1_000_000)

    with DataLink(args.host, args.port) as dl:
        dl.identify("publish_event")
        reply = dl.write(args.stream_id, t_us, t_us, payload, ack=True)

    pktid = reply.value if reply is not None else None
    print(f"published stream_id={args.stream_id} bytes={len(payload)} pktid={pktid}")
    print(json.dumps(event, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
