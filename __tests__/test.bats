##
# Install the mkdocs-multirepo-plugin locally on test run.
#
pip install -e . --quiet >&2

##
# These are helper variables and functions written in Bash. It's like writing in your Terminal!
# Feel free to optimize these, or even run them in your own Terminal.
#

rootDir=$(pwd)
fixturesDir=${rootDir}/__tests__/fixtures

debugger() {
  echo "--- STATUS ---"
  if [ $status -eq 0 ]
  then
    echo "Successful Status Code ($status)"
  else
    echo "Failed Status Code ($status)"
  fi
  echo "--- OUTPUT ---"
  echo $output
  echo "--------------"
}

assertFileExists() {
  run cat $1
  [ "$status" -eq 0 ]
}

assertFileContains() {
  run grep $2 $1
  [ "$status" -eq 0 ]
}

assertSuccessMkdocs() {
  run mkdocs $@
  debugger
  assertFileExists site/index.html
  [ "$status" -eq 0 ]
}

assertFailedMkdocs() {
  run mkdocs $@
  debugger
  [ "$status" -ne 0 ]
}

##
# These are special lifecycle methods for Bats (Bash automated testing).
# setup() is ran before every test, teardown() is ran after every test.
#

teardown() {
  rm -rf ${fixturesDir}/parent-ok-with-repos/site
  rm -rf ${fixturesDir}/parent-ok-with-nav/site
  for d in $fixturesDir/* ; do
      echo "removing $d/.git"
      rm -rf $d/.git
  done
}

setup() {
  echo "Turning imported fixtures into Git Repos for Testing-------->"
  for d in $fixturesDir/* ; do
      cd ${d}
      git init -q
      git config --global user.email "testing@example.com"
      git config --global user.name "Mr. Test"
      git add --all
      git commit -m "testing" -q
      cd ../
  done
}

##
# Test suites.
#

@test "builds a mkdocs site with multirepo repos section" {
  cd ${fixturesDir}
  run mkdocs build --config-file=parent-ok-with-repos/mkdocs.yml
  debugger
  run cat parent-ok-with-repos/site/ok-with-nav/index.html
  [[ "$output" == *"I'm an okay setup with a nav section in my docs/mkdocs.yml file."* ]]
  run cat parent-ok-with-repos/site/ok-no-nav/index.html
  [[ "$output" == *"I'm an okay setup with no nav configured in the imported repo."* ]]
}

@test "builds a mkdocs site with multirepo nav section" {
  cd ${fixturesDir}
  run mkdocs build --config-file=parent-ok-with-nav/mkdocs.yml
  debugger
  run cat parent-ok-with-nav/site/ok-with-nav/index.html
  [[ "$output" == *"I'm an okay setup with a nav section in my docs/mkdocs.yml file."* ]]
}
