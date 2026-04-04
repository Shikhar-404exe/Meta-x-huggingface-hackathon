#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_BUILD_TIMEOUT="${DOCKER_BUILD_TIMEOUT:-900}"

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { printf "%b\n" "$*"; }
pass() { printf "${GREEN}PASS${NC}: %s\n" "$*"; }
fail() { printf "${RED}FAIL${NC}: %s\n" "$*"; }
hint() { printf "hint: %s\n" "$*"; }

run_with_timeout() {
  local timeout_s="$1"
  shift
  timeout "$timeout_s" "$@"
}

log "${BOLD}Step 1/3: Running Python pre-submit checks${NC} ..."
if command -v python &>/dev/null; then
  (cd "$REPO_DIR" && python scripts/pre_submit_validate.py)
  pass "Python pre-submit checks passed"
else
  fail "python command not found"
  hint "Install Python 3.11+"
  exit 1
fi

log "${BOLD}Step 2/3: Running docker build${NC} ..."
if ! command -v docker &>/dev/null; then
  fail "docker command not found"
  hint "Install Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

if [ -f "$REPO_DIR/Dockerfile" ]; then
  DOCKER_CONTEXT="$REPO_DIR"
elif [ -f "$REPO_DIR/server/Dockerfile" ]; then
  DOCKER_CONTEXT="$REPO_DIR/server"
else
  fail "No Dockerfile found in repo root or server/ directory"
  exit 1
fi

log "  Found Dockerfile in $DOCKER_CONTEXT"

BUILD_OK=false
BUILD_OUTPUT=$(run_with_timeout "$DOCKER_BUILD_TIMEOUT" docker build "$DOCKER_CONTEXT" 2>&1) && BUILD_OK=true

if [ "$BUILD_OK" = true ]; then
  pass "Docker build succeeded"
else
  fail "Docker build failed (timeout=${DOCKER_BUILD_TIMEOUT}s)"
  printf "%s\n" "$BUILD_OUTPUT" | tail -20
  exit 1
fi

log "${BOLD}Step 3/3: Running openenv validate${NC} ..."
if ! command -v openenv &>/dev/null; then
  fail "openenv command not found"
  hint "Install it: pip install openenv-core"
  exit 1
fi

VALIDATE_OK=false
VALIDATE_OUTPUT=$(cd "$REPO_DIR" && openenv validate 2>&1) && VALIDATE_OK=true

if [ "$VALIDATE_OK" = true ]; then
  pass "openenv validate passed"
  [ -n "$VALIDATE_OUTPUT" ] && log "  $VALIDATE_OUTPUT"
else
  fail "openenv validate failed"
  printf "%s\n" "$VALIDATE_OUTPUT"
  exit 1
fi

printf "\n"
printf "${BOLD}========================================${NC}\n"
printf "${GREEN}${BOLD}  All 3/3 checks passed!${NC}\n"
printf "${GREEN}${BOLD}  Your submission is ready to submit.${NC}\n"
printf "${BOLD}========================================${NC}\n"
printf "\n"

exit 0
