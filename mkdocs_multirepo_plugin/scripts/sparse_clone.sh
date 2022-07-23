#!/bin/bash

url="$1"
docs_dir="$2"
branch=$3
shift 3
dirs=( "$@" )

if [[ -n  "$AccessToken" ]]; then
    git config http.extraheader "AUTHORIZATION: bearer $AccessToken"
fi
git clone --branch "$branch" --depth 1 --filter=blob:none --sparse $url "$docs_dir" || exit 1
cd "$docs_dir"
git sparse-checkout set --no-cone ${dirs[*]}
rm -rf .git