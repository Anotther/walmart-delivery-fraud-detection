#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! "${PYTHON_BIN}" -m bandit --version >/dev/null 2>&1; then
  echo "ERROR: bandit is not installed for ${PYTHON_BIN}."
  echo "Install dependencies with: ${PYTHON_BIN} -m pip install -r requirements.txt"
  exit 1
fi

if ! "${PYTHON_BIN}" -m pip_audit --help >/dev/null 2>&1; then
  echo "ERROR: pip-audit is not installed for ${PYTHON_BIN}."
  echo "Install dependencies with: ${PYTHON_BIN} -m pip install -r requirements.txt"
  exit 1
fi

echo "[1/3] Running Bandit security scan..."
"${PYTHON_BIN}" -m bandit -r src dashboard scripts -q

echo "[2/3] Running dependency vulnerability audit..."
"${PYTHON_BIN}" -m pip_audit -r requirements.txt

echo "[3/3] Running test suite..."
"${PYTHON_BIN}" -m pytest tests/

echo "Security checks completed successfully."
