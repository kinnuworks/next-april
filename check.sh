#!/usr/bin/env bash
# The checks that prove this project works. The session fills these in at step 5
# (HACKATHON.md): tests, typecheck, and the end-to-end script that walks the demo
# path in a real browser against the real sponsor API, recording a screen video of
# it (the rough cut for the demo video). The Stop hook in
# .claude/settings.json runs this file whenever the session tries to finish, and
# sends it back to work while anything here fails.
#
# Keep it fast enough to run often (a few minutes at most), and never make a check
# pass by skipping, weakening or special-casing it.
set -euo pipefail
cd "$(dirname "$0")"

# Fill in at step 5, for example:
# npm run typecheck
# npm test
# npx playwright test e2e/demo-path.spec.ts   (with video: 'on')

echo "check.sh: no checks yet (filled in at step 5)"
