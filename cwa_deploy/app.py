#!/usr/bin/env python3
"""Gradio UI for ringserver earthquake event JSON publish/subscribe."""

from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr

DEFAULT_HOST = os.environ.get("RINGSERVER_HOST", "")
DEFAULT_DL_PORT = int(os.environ.get("RINGSERVER_DATALINK_PORT", "16000"))
DEFAULT_HTTP_PORT = int(os.environ.get("RINGSERVER_HTTP_PORT", "18000"))
DEFAULT_STREAM_ID = "TW_DEMO_EVENT/JSON"
DEFAULT_MATCH = ".*/JSON"


def _pretty(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _client():
    # Lazy import so the Gradio UI can boot even if client deps fail at import time.
    from ringserver_client import (  # noqa: WPS433
        build_demo_event,
        fetch_http_json,
        publish_event,
        subscribe_events,
    )

    return build_demo_event, fetch_http_json, publish_event, subscribe_events


def ui_fill_demo() -> str:
    build_demo_event, *_ = _client()
    return _pretty(build_demo_event())


def ui_publish(
    host: str,
    dl_port: float,
    stream_id: str,
    payload_text: str,
    timeout: float,
) -> str:
    host = (host or "").strip()
    stream_id = (stream_id or DEFAULT_STREAM_ID).strip()
    if not host:
        return _pretty({"ok": False, "error": "Please set ringserver host (public IP/hostname)."})
    try:
        event = json.loads(payload_text)
        if not isinstance(event, dict):
            raise ValueError("JSON payload must be an object")
    except Exception as exc:  # noqa: BLE001
        return _pretty({"ok": False, "error": f"Invalid JSON payload: {exc}"})

    try:
        _, _, publish_event, _ = _client()
        result = publish_event(host, int(dl_port), stream_id, event, timeout=float(timeout))
        return _pretty(result)
    except Exception as exc:  # noqa: BLE001
        return _pretty({"ok": False, "error": str(exc)})


def ui_subscribe(
    host: str,
    dl_port: float,
    match: str,
    count: float,
    from_earliest: bool,
    timeout: float,
) -> str:
    host = (host or "").strip()
    if not host:
        return _pretty({"ok": False, "error": "Please set ringserver host (public IP/hostname)."})
    try:
        _, _, _, subscribe_events = _client()
        result = subscribe_events(
            host=host,
            port=int(dl_port),
            match=(match or DEFAULT_MATCH).strip(),
            count=int(count),
            from_earliest=bool(from_earliest),
            timeout=float(timeout),
        )
        return _pretty(result)
    except Exception as exc:  # noqa: BLE001
        return _pretty({"ok": False, "error": str(exc)})


def ui_status(host: str, http_port: float, timeout: float) -> str:
    host = (host or "").strip()
    if not host:
        return _pretty({"ok": False, "error": "Please set ringserver host (public IP/hostname)."})
    try:
        _, fetch_http_json, _, _ = _client()
        server_id = fetch_http_json(host, int(http_port), "/id/json", timeout=float(timeout))
        streams = fetch_http_json(host, int(http_port), "/streams/json", timeout=float(timeout))
        return _pretty({"id": server_id, "streams": streams})
    except Exception as exc:  # noqa: BLE001
        return _pretty({"ok": False, "error": str(exc)})


demo_event_json = _pretty(
    {
        "type": "earthquake",
        "version": 1,
        "event_id": "demo-replace-me",
        "origin_time": "2026-07-14T00:00:00Z",
        "latitude": 23.9,
        "longitude": 121.6,
        "depth_km": 10.0,
        "magnitude": 5.2,
        "magnitude_type": "ML",
        "region": "Hualien area",
        "status": "preliminary",
        "source": "cwa-deploy-gradio",
    }
)

with gr.Blocks(title="Ringserver CWA Event JSON") as demo:
    gr.Markdown(
        """
# Ringserver CWA — Event JSON Client

Publish / subscribe earthquake event JSON over **DataLink**.

> This Space is a remote client. Set a **publicly reachable** ringserver host.
> `localhost` only works when ringserver runs on the same machine as this app.
"""
    )

    with gr.Row():
        host = gr.Textbox(
            label="Ringserver host",
            value=DEFAULT_HOST,
            placeholder="e.g. ringserver.example.com or public IP",
        )
        dl_port = gr.Number(label="DataLink port", value=DEFAULT_DL_PORT, precision=0)
        http_port = gr.Number(label="HTTP port", value=DEFAULT_HTTP_PORT, precision=0)
        timeout = gr.Number(label="Timeout (seconds)", value=15, minimum=1, maximum=120)

    with gr.Tab("Publish"):
        stream_id = gr.Textbox(label="Stream ID", value=DEFAULT_STREAM_ID)
        payload = gr.Textbox(
            label="Event JSON",
            value=demo_event_json,
            lines=18,
        )
        with gr.Row():
            fill_btn = gr.Button("Fill demo event")
            publish_btn = gr.Button("Publish", variant="primary")
        publish_out = gr.Textbox(label="Publish result", lines=16)
        fill_btn.click(ui_fill_demo, outputs=payload)
        publish_btn.click(
            ui_publish,
            inputs=[host, dl_port, stream_id, payload, timeout],
            outputs=publish_out,
        )

    with gr.Tab("Subscribe"):
        match = gr.Textbox(label="Stream match (regex)", value=DEFAULT_MATCH)
        count = gr.Slider(label="Max packets", minimum=1, maximum=50, step=1, value=5)
        from_earliest = gr.Checkbox(label="From earliest buffered packet", value=False)
        subscribe_btn = gr.Button("Fetch events", variant="primary")
        subscribe_out = gr.Textbox(label="Subscribe result", lines=20)
        subscribe_btn.click(
            ui_subscribe,
            inputs=[host, dl_port, match, count, from_earliest, timeout],
            outputs=subscribe_out,
        )

    with gr.Tab("Server status"):
        status_btn = gr.Button("Query /id and /streams", variant="primary")
        status_out = gr.Textbox(label="HTTP status", lines=20)
        status_btn.click(ui_status, inputs=[host, http_port, timeout], outputs=status_out)


if __name__ == "__main__":
    # Hugging Face Spaces sets GRADIO_SERVER_NAME/PORT; keep an explicit bind as fallback.
    demo.launch(server_name="0.0.0.0", server_port=7860)
