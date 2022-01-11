#!/bin/bash

name="$1"
url="$2"
docs_dir="$3"
branch="$4"


mkdir $name # make the section directory
cd $name 
# initialize git
git init
# add extra header if the env variable exists
if [[ -n  "$AccessToken" ]]; then
    git config http.extraheader "AUTHORIZATION: bearer $AccessToken"
fi
# sparse checkout the old way
git config core.sparseCheckout true
git remote add -f origin "$url"
echo "${docs_dir}/*"> .git/info/sparse-checkout
git checkout $branch

# perfom same steps as git_docs.sh
if [ -d "$docs_dir" ]; then
    mv "$docs_dir"/* .
    root_dir=$(echo "$docs_dir" | cut -d "/" -f1)
    rm -rf "$root_dir"
    rm -rf .git
else
    rm -rf .git
    exit 1 # 1 = docs_dir doesn't exist in the branch
fi