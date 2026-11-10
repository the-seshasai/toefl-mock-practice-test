#!/usr/bin/env bash
# The checks to run before finishing any change (see .claude/CLAUDE.md).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "== backend: ruff"; (cd "$ROOT/backend" && uv run ruff check .)
echo "== backend: pytest"; (cd "$ROOT/backend" && uv run pytest -q)
echo "== frontend: lint"; (cd "$ROOT/frontend" && npm run lint)
echo "== frontend: build"; (cd "$ROOT/frontend" && npm run build)
echo "All checks passed."
