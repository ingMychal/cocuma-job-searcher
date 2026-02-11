#!/bin/bash
cd "$(dirname "$0")"
# Install deps if needed
python3 -m pip install -q -r requirements.txt 2>/dev/null || true
python3 app.py
