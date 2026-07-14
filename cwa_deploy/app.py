#!/usr/bin/env python3
"""Minimal Gradio boot check for Hugging Face Spaces."""

from __future__ import annotations

import gradio as gr


def greet(name: str) -> str:
    name = (name or "").strip() or "world"
    return f"Ringserver CWA Space is running. Hello, {name}!"


with gr.Blocks() as demo:
    gr.Markdown("# Ringserver CWA — boot check")
    name = gr.Textbox(label="Name", value="CWA")
    out = gr.Textbox(label="Output")
    btn = gr.Button("Test", variant="primary")
    btn.click(greet, inputs=name, outputs=out)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
