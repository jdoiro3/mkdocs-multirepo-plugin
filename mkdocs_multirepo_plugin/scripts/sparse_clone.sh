#!/bin/bash

url="$1"
docs_dir="$2"
branch=$3
shift 3
dirs=( "$@" )

protocol="$(echo "$url" | sed 's/:\/\/.*//')"
url_rest="$(echo "$url" | sed 's/.*:\/\///')"

if [[ -n  "$AccessToken" ]]; then
    url_to_use="${protocol}://$AccessToken@$url_rest"
    git config http.extraheader "AUTHORIZATION: bearer $AccessToken"
elif [[ -n  "$GithubAccessToken" ]]; then
    url_to_use="${protocol}://x-access-token:$GithubAccessToken@$url_rest"
else
  url_to_use="$url"
fi

git clone --branch "$branch" --depth 1 --filter=blob:none --sparse $url_to_use "$docs_dir" || exit 1
cd "$docs_dir" || exit 1
git sparse-checkout set --no-cone ${dirs[*]}
rm -rf .git