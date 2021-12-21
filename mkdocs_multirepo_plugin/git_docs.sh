#!/bin/bash

name="$1"
url="$2"
docs_dir="$3"
branch="$4"

git clone --branch $branch --depth 1 --filter=blob:none --sparse $url "$name" || exit 2
cd "$name"
git sparse-checkout set "${docs_dir}/*"

if [ -d $docs_dir ]; then
    cd $docs_dir
    mv * ../
    cd ../
    rm -rf "$docs_dir"
    rm -rf .git
else
    rm -rf .git
    exit 1 # 1 = docs_dir doesn't exist in the branch
fi
