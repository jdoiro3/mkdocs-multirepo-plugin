##
# These are helper variables and functions written in Bash. It's like writing in your Terminal!
# Feel free to optimize these, or even run them in your own Terminal.
#

rootDir=$(pwd)
fixturesDir=${rootDir}/__tests__/fixtures

debugger() {
  echo "--- STATUS ---"
  if [ $status -eq 0 ]; then
    echo "Successful Status Code ($status)"
  else
    echo "Failed Status Code ($status)"
  fi
  echo "--- OUTPUT ---"
  echo $output
}

outputContains() {
  if [[ "$output" == *"$1"* ]]
  then
    return 0
  else
    echo "Output does not contain '$1'"
    echo "--- OUTPUT ---"
    echo "$output"
    return 1
  fi
}

assertFileExists() {
  if test -f "$1"; then
    return 0
  else
    echo "$1 does not exist"
    echo "--- Site Directory Contents ---"
    tree "$parent/site"
    return 1
  fi
}

assertFileDoesntExist() {
  if ! test -f "$1"; then
    return 0
  else
    return 1
  fi
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
      rm -rf ${d}/site
  done
}

##
# Test suites.
#

@test "Build a mkdocs site with repos section" {
  cd ${fixturesDir}
  parent="parent-with-repos"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat "$parent/site/ok-nav-simple/index.html"
  outputContains "Welcome to a simple repo."
  run cat "$parent/site/ok-no-nav/index.html"
  outputContains "I'm an okay setup with no nav configured in the imported repo."
  run cat "$parent/site/ok-nav-complex/index.html"
  outputContains "Welcome to a complex repo."
  run cat "$parent/site/ok-nav-complex/section1/getting-started/index.html"
  outputContains "Let's get started with section 1."
  run cat "$parent/site/ok-nav-complex/section2/getting-started/index.html"
  outputContains "Let's get started with section 2."
  run cat "$parent/site/ok-nav-complex/section1/index.html"
  outputContains "Welcome to section 1."
  run cat "$parent/site/ok-nav-complex/section2/index.html"
  outputContains "Welcome to section 2."
  run cat "$parent/site/sub-section/deep/ok-sub-section/index.html"
  outputContains "Welcome to a simple repo."
}

@test "Build a mkdocs site with nav section" {
  cd ${fixturesDir}
  parent="parent-with-nav"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  assertFileExists "$parent/site/ok-nav-simple/index.html"
  run cat "$parent/site/ok-nav-simple/index.html"
  outputContains "Welcome to a simple repo."
}

@test "Build a mkdocs site with nav section using material's indexes nav" {
  cd ${fixturesDir}
  parent="parent-with-indexes-nav"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  assertFileExists "$parent/site/ok-nav-simple/index.html"
  run cat "$parent/site/ok-nav-simple/index.html"
  outputContains "Welcome to a simple repo."
}

@test "Build a mkdocs site with a different config file name and location" {
  cd ${fixturesDir}
  parent="parent-config-test"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  assertFileExists "$parent/site/section/index.html"
  run cat "$parent/site/section/index.html"
  outputContains "I'm okay even though my config file is outside the docs folder and is called multirepo.yml"
}

@test "Build a mkdocs site with multiple imports in nav section" {
  cd ${fixturesDir}
  parent="parent-multiple-nav-imports"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  run cat "$parent/site/ok-nav-simple/index.html"
  outputContains "Welcome to a simple repo."
  run cat "$parent/site/ok-nav-complex/index.html"
  outputContains "Welcome to a complex repo."
  run cat "$parent/site/ok-nav-complex/section1/getting-started/index.html"
  outputContains "Let's get started with section 1."
  run cat "$parent/site/ok-nav-complex/section2/getting-started/index.html"
  outputContains "Let's get started with section 2."
  run cat "$parent/site/ok-nav-complex/section1/index.html"
  outputContains "Welcome to section 1."
  run cat "$parent/site/ok-nav-complex/section2/index.html"
  outputContains "Welcome to section 2."
}

@test "Build a mkdocs site with subsection imports with same section names" {
  cd ${fixturesDir}
  parent="parent-multiple-nav-imports"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  # testing subsection import
  assertFileExists "$parent/site/section/ok-nav-simple/index.html"
  run cat "$parent/site/section/ok-nav-simple/index.html"
  outputContains "Welcome to a simple repo."

  assertFileExists "$parent/site/section/ok-nav-complex/index.html"
  run cat "$parent/site/section/ok-nav-complex/index.html"
  outputContains "Welcome to a complex repo."

  assertFileExists "$parent/site/section/ok-nav-complex/section1/getting-started/index.html"
  run cat "$parent/site/section/ok-nav-complex/section1/getting-started/index.html"
  outputContains "Let's get started with section 1."

  assertFileExists "$parent/site/section/ok-nav-complex/section2/getting-started/index.html"
  run cat "$parent/site/section/ok-nav-complex/section2/getting-started/index.html"
  outputContains "Let's get started with section 2."

  assertFileExists "$parent/site/section/ok-nav-complex/section1/index.html"
  run cat "$parent/site/section/ok-nav-complex/section1/index.html"
  outputContains "Welcome to section 1."

  assertFileExists "$parent/site/section/ok-nav-complex/section2/index.html"
  run cat "$parent/site/section/ok-nav-complex/section2/index.html"
  outputContains "Welcome to section 2."

  # testing an import within multiple subsections
  assertFileExists "$parent/site/deepimport/subsection/subsection/ok-nav-simple/index.html"
  run cat "$parent/site/deepimport/subsection/subsection/ok-nav-simple/index.html"
  outputContains "Welcome to a simple repo."
}

@test "Make sure imported repo's mkdocs.yml isn't in build output" {
  cd ${fixturesDir}
  parent="parent-confirm-no-mkdocs.yml"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  assertFileDoesntExist "$parent/site/DemoRepo/mkdocs.yml"
}

@test "Make sure imported repo's with images are included in build output" {
  cd ${fixturesDir}
  parent="parent-with-imported-images"
  run mkdocs build --config-file=$parent/mkdocs.yml
  debugger
  assertFileExists "$parent/site/ok-with-images/assets/images/zelda-dark-world.png"
}

@test "Build a mkdocs site with nav_repos" {
  cd ${fixturesDir}
  parent="parent-with-nav-repos"
  run mkdocs build --config-file=$parent/mkdocs.yml

  debugger
  assertFileExists "$parent/site/index.html"
  run cat "$parent/site/index.html"
  outputContains "Main page of parent repo."

  assertFileExists "$parent/site/repo1/index.html"
  run cat "$parent/site/repo1/index.html"
  outputContains "Used to demo the"

  assertFileExists "$parent/site/repo1/docs/page1/index.html"
  run cat "$parent/site/repo1/docs/page1/index.html"
  outputContains "Welcome to Page1"

  assertFileExists "$parent/site/repo1/docs/page2/index.html"
  run cat "$parent/site/repo1/docs/page2/index.html"
  outputContains "Welcome to Page2"

  assertFileExists "$parent/site/repo2/index.html"
  run cat "$parent/site/repo2/index.html"
  outputContains "Used to demo the"

  assertFileExists "$parent/site/repo2/index.html"
  run cat "$parent/site/repo2/index.html"
  outputContains "Used to demo the"

  assertFileExists "$parent/site/repo3/index.html"
  run cat "$parent/site/repo3/index.html"
  outputContains "Welcome to a simple repo."
}
