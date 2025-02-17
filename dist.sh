#!/usr/bin/env sh

APP="loradio"

DIR=$(dirname "$0")
cd "${DIR}" || exit

echo "build distr"

echo "create release dir if not exists"
mkdir -p release

echo "clear release dir"
rm -rf release/* || exit

echo "copy run-xxx.sh"
cp run-*.sh release || exit

echo "copy config"
cp -r config release || exit

echo "copy README"
cp README.md release || exit

echo "copy dist"
cp -r .build/main.dist release || exit
mv release/main.dist release/dist || exit

echo "zip"
filename=$(date +"${APP}-%Y-%m-%d.zip")
rm -f filename
cd release || exit
zip -q -r "../$filename" . "*"
echo "${filename}"

echo "SHA-1 checksum"
sha1sum "../$filename"

echo "done"
