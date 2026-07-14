"""Shared helpers for ringserver event JSON publish/subscribe."""

from __future__ import annotations

import json
import socket
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from datalink_client import DataLink, DataLinkError

DEFAULT_STREAM_ID = "TW_DEMO_EVENT/JSON"
DEFAULT_MATCH = ".*/JSON"


def build_demo_event(event_id: str | None = None) -> dict[str, Any]:
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
        "source": "cwa-deploy-gradio",
    }


def publish_event(
    host: str,
    port: int,
    stream_id: str,
    event: dict[str, Any],
    timeout: float = 10.0,
) -> dict[str, Any]:
    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    t_us = int(time.time() * 1_000_000)

    with DataLink(host, int(port), timeout=timeout) as dl:
        server_id = dl.identify("cwa_publish")
        reply = dl.write(stream_id, t_us, t_us, payload, ack=True)

    return {
        "ok": True,
        "server_id": server_id,
        "stream_id": stream_id,
        "bytes": len(payload),
        "pktid": reply.value if reply is not None else None,
        "event": event,
    }


def subscribe_events(
    host: str,
    port: int,
    match: str = DEFAULT_MATCH,
    count: int = 5,
    from_earliest: bool = False,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Collect up to `count` matching packets, then stop.

    Uses a socket timeout so the UI does not hang forever when no events arrive.
    """
    count = max(1, int(count))
    events: list[dict[str, Any]] = []
    error: str | None = None

    try:
        with DataLink(host, int(port), timeout=timeout) as dl:
            server_id = dl.identify("cwa_subscribe")
            dl.match(match)
            if from_earliest:
                dl.position_set("EARLIEST")
            else:
                dl.set_position_latest()
            dl.stream()

            try:
                for packet in dl.collect():
                    item: dict[str, Any] = {
                        "stream_id": packet.streamid,
                        "pktid": packet.pktid,
                    }
                    try:
                        item["event"] = json.loads(packet.data.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        item["raw_error"] = str(exc)
                        item["raw_bytes"] = len(packet.data)
                    events.append(item)
                    if len(events) >= count:
                        break
            except (TimeoutError, socket.timeout):
                pass
            except DataLinkError as exc:
                # Timeout while waiting for the next packet is expected.
                if "timed out" not in str(exc).lower() and "timeout" not in str(exc).lower():
                    error = str(exc)
            finally:
                if dl.is_streaming:
                    try:
                        dl.endstream(timeout=min(5.0, timeout))
                    except Exception:
                        pass

        return {
            "ok": error is None,
            "server_id": server_id,
            "match": match,
            "received": len(events),
            "events": events,
            "error": error,
            "note": None
            if events
            else "No packets received before timeout. Publish an event or increase timeout.",
        }
    except Exception as exc:  # noqa: BLE001 - surface to Gradio UI
        return {
            "ok": False,
            "server_id": None,
            "match": match,
            "received": len(events),
            "events": events,
            "error": str(exc),
            "note": "Connection or protocol error. Check host/port and WriteIP/network access.",
        }


def fetch_http_json(host: str, http_port: int, path: str, timeout: float = 10.0) -> dict[str, Any]:
    url = f"http://{host}:{int(http_port)}{path}"
    try:
        with urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
        return {"ok": True, "url": url, "data": json.loads(body)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "url": url, "error": str(exc)}
