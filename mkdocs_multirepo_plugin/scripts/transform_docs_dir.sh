docs_dir="$1"

echo $docs_dir
if [ -d "$docs_dir" ]; then
    mv "$docs_dir"/* . # move everything in docs directory to the root
    root_dir=$(echo "$docs_dir" | cut -d "/" -f1)
    rm -rf "$root_dir"
else
    exit 1 # 1 = docs_dir doesn't exist in the branch
fi