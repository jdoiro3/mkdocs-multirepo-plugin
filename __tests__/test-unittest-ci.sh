#!/bin/bash

# Lint via flake8
printf "Running flake8 linter -------->\n"
printf "flake8 count for E9,F63,F7,F82: "
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=setup.py,env
printf "flake8 count for max-complexity=10: "
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=setup.py,env,tests

# End-to-end testing via Bats (Bash automated tests)
GITHUB_ACTIONS_E2E_PATH="/home/runner/work/mkdocs-multirepo-plugin/mkdocs_multirepo_plugin/__tests__/test.bats"
LOCAL_E2E_PATH="./__tests__/test.bats"

if [[ -f "$GITHUB_ACTIONS_E2E_PATH" ]]; then
    bats $GITHUB_ACTIONS_E2E_PATH
elif [[ -f "$LOCAL_E2E_PATH" ]]; then
    bats $LOCAL_E2E_PATH
else
    echo "Could not find the test.bats file. Please check /__tests__/test-ci.sh and correct the paths."
    exit 1
fi

# Running unit-tests
python3 -m unittest tests.unittests
