#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "[run.sh] Starting agent..."
python3 agent.py

echo "[run.sh] Publishing site..."
python3 publish.py

echo "[run.sh] Syncing Notion..."
python3 notion_sync.py

echo "[run.sh] Committing and pushing..."
git add -A
git commit -m "Daily update $(date +%Y-%m-%d)"
git push

echo "[run.sh] Done."
