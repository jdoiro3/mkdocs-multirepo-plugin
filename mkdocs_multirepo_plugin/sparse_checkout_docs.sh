#!/bin/bash

YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

name=$1
url=$2
docs_dir=$3
branch=$4
root_docs_dir=$5

printf "${YELLOW}INFO${NC}: Pulling documentation from ${url} into ${root_docs_dir}/$name\n"
cd $root_docs_dir
mkdir -p $name
cd $name
git init --quiet
git config core.sparseCheckout true
git remote add -f origin "$url"
echo "${docs_dir}/*"> .git/info/sparse-checkout
git checkout --quiet $branch

if [ -d $docs_dir ]; then
    cd $docs_dir
    mv * ../
    cd ../
    rm -rf $docs_dir
else
    printf "${RED}WARNING${NC}: ${docs_dir} directory doesn't exist in ${branch}"
fi

rm -rf .git