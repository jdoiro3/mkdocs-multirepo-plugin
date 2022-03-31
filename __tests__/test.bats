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

assertFileDoesntExist() {
  run cat $1
  [ "$status" -eq 1 ]
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
  for d in $fixturesDir/* ; do
      echo "removing $d/.git"
      rm -rf $d/.git
      echo "removing $d/site"
      rm -rf ${d}/site
  done
}

setup() {
  echo "Turning imported fixtures into Git Repos for Testing-------->"
  for d in $fixturesDir/* ; do
      cd ${d}
      git init -q
      git config user.email "testing@example.com"
      git config user.name "Mr. Test"
      git add --all
      git commit -m "testing" -q
      cd ../
  done
}

##
# Test suites.
#

@test "Local Repo Test: builds a mkdocs site with repos section" {
  cd ${fixturesDir}
  parent="parent-with-repos"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat $parent/site/ok-nav-simple/index.html
  [[ "$output" == *"Welcome to a simple repo."* ]]
  debugger
  run cat $parent/site/ok-no-nav/index.html
  [[ "$output" == *"I'm an okay setup with no nav configured in the imported repo."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/index.html
  [[ "$output" == *"Welcome to a complex repo."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section1/getting-started/index.html
  [[ "$output" == *"Let's get started with section 1."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section2/getting-started/index.html
  [[ "$output" == *"Let's get started with section 2."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section1/index.html
  [[ "$output" == *"Welcome to section 1."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section2/index.html
  [[ "$output" == *"Welcome to section 2."* ]]
  debugger
}

@test "Local Repo Test: builds a mkdocs site with nav section" {
  cd ${fixturesDir}
  parent="parent-with-nav"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat $parent/site/ok-nav-simple/index.html
  [[ "$output" == *"Welcome to a simple repo."* ]]
  debugger
}

@test "Local Repo Test: builds a mkdocs site with a different config file name and location" {
  cd ${fixturesDir}
  parent="parent-config-test"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat $parent/site/section/index.html
  [[ "$output" == *"I'm okay even though my config file is outside the docs folder and is called multirepo.yml"* ]]
  debugger
}

@test "Local Repo Test: builds a mkdocs site with multiple imports in nav section" {
  cd ${fixturesDir}
  parent="parent-multiple-nav-imports"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat $parent/site/ok-nav-simple/index.html
  [[ "$output" == *"Welcome to a simple repo."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/index.html
  [[ "$output" == *"Welcome to a complex repo."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section1/getting-started/index.html
  [[ "$output" == *"Let's get started with section 1."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section2/getting-started/index.html
  [[ "$output" == *"Let's get started with section 2."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section1/index.html
  [[ "$output" == *"Welcome to section 1."* ]]
  debugger
  run cat $parent/site/ok-nav-complex/section2/index.html
  [[ "$output" == *"Welcome to section 2."* ]]
  debugger
  # testing subsection import
  run cat $parent/site/ok-nav-simple2/index.html
  [[ "$output" == *"Welcome to a simple repo."* ]]
  debugger
  run cat $parent/site/ok-nav-complex2/index.html
  [[ "$output" == *"Welcome to a complex repo."* ]]
  debugger
  run cat $parent/site/ok-nav-complex2/section1/getting-started/index.html
  [[ "$output" == *"Let's get started with section 1."* ]]
  debugger
  run cat $parent/site/ok-nav-complex2/section2/getting-started/index.html
  [[ "$output" == *"Let's get started with section 2."* ]]
  debugger
  run cat $parent/site/ok-nav-complex2/section1/index.html
  [[ "$output" == *"Welcome to section 1."* ]]
  debugger
  run cat $parent/site/ok-nav-complex2/section2/index.html
  [[ "$output" == *"Welcome to section 2."* ]]
  debugger
  # testing an import within multiple subsections
  run cat $parent/site/ok-nav-simple3/index.html
  [[ "$output" == *"Welcome to a simple repo."* ]]
  debugger
}

@test "Github Tests: builds a mkdocs site with multiple imports in nav section" {
  cd ${fixturesDir}
  parent="parent-multiple-nav-imports-github"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat $parent/site/DemoRepo/index.html
  [[ "$output" == *"Wow, isn't that really cool. It's all done in one line."* ]]
  debugger
  run cat $parent/site/DemoRepo2/index.html
  [[ "$output" == *"Wow, isn't that really cool. It's all done in one line."* ]]
  debugger
}

@test "Github Tests: Make sure imported repo's mkdocs.yml isn't in build output" {
  cd ${fixturesDir}
  parent="parent-confirm-no-mkdocs.yml-github"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  assertFileDoesntExist $parent/site/DemoRepo/mkdocs.yml
}
