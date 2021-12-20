#!/bin/bash

name="$1"
url="$2"
docs_dir="$3"
branch="$4"
temp_dir="$5"

cd $temp_dir
mkdir -p "$name"
git clone --branch $branch --depth 1 --filter=blob:none --sparse $url "$name"
cd "$name"
git sparse-checkout set "${docs_dir}/*"

if [ -d $docs_dir ]; then
    cd $docs_dir
    mv * ../
    cd ../
    rm -rf $docs_dir
    rm -rf .git
else
    rm -rf .git
    exit 1 # 1 = docs_dir doesn't exist in the branch
fi
