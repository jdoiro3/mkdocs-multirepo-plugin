#!/bin/bash

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
