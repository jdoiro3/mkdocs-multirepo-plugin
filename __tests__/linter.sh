#!/bin/bash

# Lint via flake8
printf "Running flake8 linter -------->\n"
printf "flake8 count for E9,F63,F7,F82: "
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=setup.py,env
printf "flake8 count for max-complexity=10: "
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=setup.py,env,tests
