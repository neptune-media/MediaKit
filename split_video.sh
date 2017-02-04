#!/bin/bash

[ -z "$1" ] && echo "usage: $0 input" && exit 1
INPUT="$1"
shift

set -ex

./extract_iframes.sh "${INPUT}" "${INPUT}".frames

./find_chapter_splits.py --iframes "${INPUT}".frames --output output.mkv "${INPUT}" $@ | sh
for i in $(ls output-*.mkv)
do
  ./renumber_chapters.sh "$i"
done

