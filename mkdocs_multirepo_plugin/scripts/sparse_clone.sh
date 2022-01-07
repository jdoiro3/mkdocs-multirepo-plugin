#!/bin/bash

url="$1"
name="$2"
branch=$3
shift 3
dirs=( "$@" )
echo "${dirs[*]}"

if [[ -n  "$AccessToken" ]]; then
    git config http.extraheader "AUTHORIZATION: bearer $AccessToken"
fi
git clone --branch "$branch" --depth 1 --filter=blob:none --sparse $url "$name"
cd "$name"
git sparse-checkout set ${dirs[*]}
rm -rf .git