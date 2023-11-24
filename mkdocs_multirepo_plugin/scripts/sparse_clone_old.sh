#!/bin/bash
set -f

url="$1"
docs_dir="$2"
branch=$3
shift 3
dirs=( "$@" )


mkdir -p "$docs_dir" # make the section directory
cd "$docs_dir"
# initialize git
git init

protocol="$(echo "$url" | sed 's/:\/\/.*//')"
url_rest="$(echo "$url" | sed 's/.*:\/\///')"

if [[ -n  "$AccessToken" ]]; then
    url_to_use="${protocol}://$AccessToken@$url_rest"
    git config http.extraheader "AUTHORIZATION: bearer $AccessToken"
elif [[ -n  "$GithubAccessToken" ]]; then
    url_to_use="${protocol}://x-access-token:$GithubAccessToken@$url_rest"
elif [[ -n  "$BitbucketAcessToken" ]]; then
    url_to_use="$url"
    git config http.extraheader "AUTHORIZATION: Bearer $BitbucketAcessToken"
else
  url_to_use="$url"
fi
# sparse checkout the old way
git config core.sparseCheckout true
git remote add -f origin "$url_to_use"
# .git/info might not exist after git init, depending on git version
# (e.g. git 2.24.1 does not create it)
mkdir -p .git/info
for dir in "${dirs[@]}"
do
   printf "${dir}\n">> .git/info/sparse-checkout
done
git checkout $branch
rm -rf .git
