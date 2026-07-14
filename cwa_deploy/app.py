#!/usr/bin/env python3
"""Gradio UI for ringserver earthquake event JSON publish/subscribe."""

from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr

from ringserver_client import (
    DEFAULT_MATCH,
    DEFAULT_STREAM_ID,
    build_demo_event,
    fetch_http_json,
    publish_event,
    subscribe_events,
)

DEFAULT_HOST = os.environ.get("RINGSERVER_HOST", "")
DEFAULT_DL_PORT = int(os.environ.get("RINGSERVER_DATALINK_PORT", "16000"))
DEFAULT_HTTP_PORT = int(os.environ.get("RINGSERVER_HTTP_PORT", "18000"))


def _pretty(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def ui_fill_demo() -> str:
    return _pretty(build_demo_event())


def ui_publish(
    host: str,
    dl_port: int,
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
        result = publish_event(host, int(dl_port), stream_id, event, timeout=float(timeout))
        return _pretty(result)
    except Exception as exc:  # noqa: BLE001
        return _pretty({"ok": False, "error": str(exc)})


def ui_subscribe(
    host: str,
    dl_port: int,
    match: str,
    count: int,
    from_earliest: bool,
    timeout: float,
) -> str:
    host = (host or "").strip()
    if not host:
        return _pretty({"ok": False, "error": "Please set ringserver host (public IP/hostname)."})
    result = subscribe_events(
        host=host,
        port=int(dl_port),
        match=(match or DEFAULT_MATCH).strip(),
        count=int(count),
        from_earliest=bool(from_earliest),
        timeout=float(timeout),
    )
    return _pretty(result)


def ui_status(host: str, http_port: int, timeout: float) -> str:
    host = (host or "").strip()
    if not host:
        return _pretty({"ok": False, "error": "Please set ringserver host (public IP/hostname)."})
    server_id = fetch_http_json(host, int(http_port), "/id/json", timeout=float(timeout))
    streams = fetch_http_json(host, int(http_port), "/streams/json", timeout=float(timeout))
    return _pretty({"id": server_id, "streams": streams})


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
        payload = gr.Code(
            label="Event JSON",
            language="json",
            value=_pretty(build_demo_event()),
            lines=18,
        )
        with gr.Row():
            fill_btn = gr.Button("Fill demo event")
            publish_btn = gr.Button("Publish", variant="primary")
        publish_out = gr.Code(label="Publish result", language="json", lines=16)
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
        subscribe_out = gr.Code(label="Subscribe result", language="json", lines=20)
        subscribe_btn.click(
            ui_subscribe,
            inputs=[host, dl_port, match, count, from_earliest, timeout],
            outputs=subscribe_out,
        )

    with gr.Tab("Server status"):
        status_btn = gr.Button("Query /id and /streams", variant="primary")
        status_out = gr.Code(label="HTTP status", language="json", lines=20)
        status_btn.click(ui_status, inputs=[host, http_port, timeout], outputs=status_out)

    gr.Markdown(
        """
### Tips
- ringserver config should set `MaxPacketSize` large enough for your JSON (e.g. 65536)
- writers need `WriteIP` permission on the server
- HF Space outbound access must reach your DataLink/HTTP ports
"""
    )


if __name__ == "__main__":
    demo.launch()
