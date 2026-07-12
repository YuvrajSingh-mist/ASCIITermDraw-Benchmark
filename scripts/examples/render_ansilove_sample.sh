#!/usr/bin/env bash
set -euo pipefail

input="${1:-oneshot/c3_example.txt}"
ascii_copy="${2:-oneshot/c3_example_ansilove.asc}"
output="${3:-oneshot/c3_example_ansilove.png}"

cp "$input" "$ascii_copy"
ansilove "$ascii_copy"
mv "${ascii_copy}.png" "$output"
echo "Rendered $input -> $output via AnsiLove"
