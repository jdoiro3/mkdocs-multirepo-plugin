#!/bin/bash

# Note: testing inspired by mkdocs-monorepo-plugin

# Lint via flake8
printf "Running flake8 linter -------->\n"
printf "flake8 count for E9,F63,F7,F82: "
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=setup.py,env,tests
printf "flake8 count for max-complexity=10: "
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=setup.py,env,tests

# End-to-end testing via Bats (Bash automated tests)
function docker_run_integration_tests() {
docker build -t mkdocs-multirepo-test-runner:$1 --quiet -f- . <<EOF
  FROM python:$1
  ENV VIRTUAL_ENV=env
  RUN python3 -m venv $VIRTUAL_ENV
  ENV PATH="$VIRTUAL_ENV/bin:$PATH"
  COPY ./requirements.txt /workspace/requirements.txt
  RUN apt-get -y update && apt-get -yyy install bats && apt-get -yyy install git
  RUN pip install --upgrade pip
  RUN pip install -r /workspace/requirements.txt
  ENTRYPOINT ["bats"]
  CMD ["/workspace/__tests__/test.bats"]
EOF

printf "\nRunning E2E tests via Bats in Docker (python:$1) -------->\n"
docker run -it -w /workspace -v $(pwd):/workspace mkdocs-multirepo-test-runner:$1
}

if [[ ! -z "$PYTHON_37_ONLY" ]]; then
  docker_run_integration_tests "3.7-slim"
else
  docker_run_integration_tests "3-slim"
  docker_run_integration_tests "3.6-slim"
  docker_run_integration_tests "3.7-slim"
fi