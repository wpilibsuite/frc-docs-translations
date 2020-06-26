#!/bin/sh
# update transifex pot and local po files

set -ex

LANG_TO_PULL=${1:-'fr_CA,es_MX'}
LANG_MAP='es_MX: es, fr_CA: fr, he_IL: he, tr_TR: tr'
MAINPROJECT=frc-docs

# Set working directory to repo root
cd `dirname $0`/..

# Update submodule
git submodule update --recursive --remote

# Create POT Files
sphinx-build -T -b gettext $MAINPROJECT/source locale/pot

# Update .tx/config
mv .tx/config .tx/config.old
sphinx-intl create-txconfig
echo "lang_map = ${LANG_MAP}" >> .tx/config
sphinx-intl update-txconfig-resources -p locale/pot -d locale --transifex-project-name $MAINPROJECT
# TODO: Compare new and old configs and lock or remove deleted files on transifex
rm .tx/config.old

# Push and pull from Transifex. It is important to push then pull!
# If you pull then push, the PO files will contain out of date strings.
if [ "$CI" = true ]
then
    tx push --source --no-interactive --skip
fi
tx pull -l $LANG_TO_PULL --mode onlyreviewed --use-git-timestamps
