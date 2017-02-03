#!/bin/bash

[ -z "$2" ] && echo "usage: $0 input output" && exit 1
INPUT="$1"
OUTPUT="$2"
ffprobe -select_streams v -show_frames -of csv "${INPUT}" | awk -F, '/I/ {print $5}' > "${OUTPUT}"
