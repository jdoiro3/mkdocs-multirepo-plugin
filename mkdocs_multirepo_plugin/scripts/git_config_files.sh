#!/bin/bash

url="$1"
custom_dir="$2"
yml_file="$3"
branch="$4"
config_file="$5"

if [[ -n  "$AccessToken" ]]; then
    git config http.extraheader "AUTHORIZATION: bearer $AccessToken"
fi
git clone --branch $branch --depth 1 --filter=blob:none --sparse $url "overrides" || exit 2
cd "overrides"
git sparse-checkout set "${custom_dir}/*" "${yml_file}"

if [ -d "$custom_dir" ] && [ -f  "$yml_file" ]; then
    shopt -s dotglob
    mv "$custom_dir"/* .
    mv "$yml_file" .
    mv "mkdocs.yml" ../"$config_file"
    root_dir=$(echo "$custom_dir" | cut -d "/" -f1)
    rm -rf "$root_dir"
    rm -rf .git
else
    rm -rf .git
    exit 1
fi