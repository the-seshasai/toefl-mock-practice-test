#!/usr/bin/env bash
# First-time setup on Ubuntu: checks tools, installs dependencies, creates .env, downloads the speech models.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1. $2" >&2; exit 1; }; }
need uv "Install it from https://docs.astral.sh/uv/ (curl -LsSf https://astral.sh/uv/install.sh | sh)"
need node "Install Node.js 20 or newer (for example from https://nodejs.org or via nvm)."
need npm "Comes with Node.js."
need claude "Install Claude Code and run 'claude' once to log in: https://claude.com/claude-code"
python3 - <<'PY' || { echo "Python 3.11+ is required (uv can install one: uv python install 3.12)." >&2; exit 1; }
import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)
PY
node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' || { echo "Node 20+ is required." >&2; exit 1; }

echo "== Backend dependencies"
(cd backend && uv sync)
echo "== Frontend dependencies"
(cd frontend && npm ci)
[[ -f .env ]] || { cp .env.example .env; echo "Created .env from .env.example"; }
echo "== Speech models"
"$ROOT/scripts/download_models.sh" "$@"
echo
echo "Setup complete. Start the app with: scripts/run_dev.sh"
