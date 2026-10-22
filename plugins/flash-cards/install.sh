#!/usr/bin/env bash

set -euo pipefail

rm -rf venv voices
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m piper.download_voices --download-dir voices ko_KR-kss-medium
