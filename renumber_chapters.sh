#!/bin/bash

[ -z "$1" ] && echo "usage: $0 filename" && exit 1
FILE="$1"

mkvextract chapters -s "${FILE}" | sed -re 's/^(CHAPTER([0-9]+)NAME)=.*$/\1=Chapter \2/g' > "${FILE}".chapters
mkvpropedit "${FILE}" -c "${FILE}".chapters
rm -f "${FILE}".chapters
