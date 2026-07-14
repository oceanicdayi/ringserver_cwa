---
title: Ringserver Cwa
emoji: 💻
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: 6.20.0
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Event JSON publish/subscribe for ringserver
---

# Ringserver CWA — Event JSON Client

Gradio client for earthquake **event JSON** streaming via ringserver DataLink.

Space: https://huggingface.co/spaces/oceanicdayi/Ringserver_cwa

## Features

- **Publish** event JSON to a stream (default `TW_DEMO_EVENT/JSON`)
- **Subscribe / fetch** matching `/JSON` packets
- **Server status** via HTTP `/id/json` and `/streams/json`

## Local Gradio

```bash
cd cwa_deploy
python3 -m pip install -r requirements.txt
python3 app.py
```

## Local CLI (optional)

```bash
# start ringserver from this directory
mkdir -p ring
../ringserver ring-event.conf

python3 subscribe_events.py
python3 publish_event.py
```

## Deploy / update Hugging Face Space

Requires a Hugging Face write token (`HF_TOKEN`):

```bash
export HF_TOKEN=hf_xxx
python3 deploy_hf_space.py
```

Or:

```bash
huggingface-cli upload oceanicdayi/Ringserver_cwa . \
  --repo-type=space \
  --commit-message "Update Gradio event JSON client"
```

## Notes

- On Hugging Face, set a **public** ringserver host; `localhost` will not reach your private server.
- Ensure ringserver `MaxPacketSize` is large enough for event JSON.
- DataLink writers must be allowed via `WriteIP` / auth.
