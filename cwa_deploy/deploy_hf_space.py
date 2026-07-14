#!/usr/bin/env python3
"""Upload cwa_deploy Gradio app files to Hugging Face Space.

Usage:
  export HF_TOKEN=hf_xxx   # write access token
  python3 deploy_hf_space.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from shutil import copy2

from huggingface_hub import HfApi, login

SPACE_ID = os.environ.get("HF_SPACE_ID", "oceanicdayi/Ringserver_cwa")
ROOT = Path(__file__).resolve().parent

# Files that make up the Space root.
UPLOAD_FILES = [
    "app.py",
    "ringserver_client.py",
    "publish_event.py",
    "subscribe_events.py",
    "requirements.txt",
    "README.md",
    "ring-event.conf",
]


def main() -> int:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if not token:
        msg = (
            "HF_TOKEN is not set.\n"
            "Create a write token at https://huggingface.co/settings/tokens\n"
            "then: export HF_TOKEN=hf_...\n"
            "       python3 deploy_hf_space.py"
        )
        if os.environ.get("SKIP_IF_NO_TOKEN") == "1":
            print(msg)
            print("SKIP_IF_NO_TOKEN=1 set; exiting without error.")
            return 0
        print(msg, file=sys.stderr)
        return 1

    missing = [name for name in UPLOAD_FILES if not (ROOT / name).is_file()]
    if missing:
        print(f"Missing files: {missing}", file=sys.stderr)
        return 1

    login(token=token)
    api = HfApi(token=token)

    with tempfile.TemporaryDirectory(prefix="hf-space-") as tmp:
        tmp_path = Path(tmp)
        for name in UPLOAD_FILES:
            copy2(ROOT / name, tmp_path / name)

        print(f"Uploading {len(UPLOAD_FILES)} files to space {SPACE_ID} ...")
        api.upload_folder(
            folder_path=str(tmp_path),
            repo_id=SPACE_ID,
            repo_type="space",
            commit_message="Deploy Gradio event JSON client for ringserver CWA",
        )

    # Force a clean rebuild/start when the Space is stuck initializing.
    print(f"Factory-rebooting space {SPACE_ID} ...")
    runtime = api.restart_space(repo_id=SPACE_ID, factory_reboot=True)
    print(f"Restart requested; stage={getattr(runtime, 'stage', runtime)}")

    print(f"Done. Open https://huggingface.co/spaces/{SPACE_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
