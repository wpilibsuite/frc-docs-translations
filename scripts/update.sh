#!/bin/sh
# update transifex pot and local po files

set -ex

LANG_TO_PULL=${1:-'fr_CA,es_MX,zh_CN,tr_TR,he_IL,pt,ja'}
LANG_MAP='es_MX: es, fr_CA: fr, he_IL: he, tr_TR: tr'
MAINPROJECT=frc-docs
ORGANIZATION=wpilib

# Set working directory to repo root
cd `dirname $0`/..

# Create POT Files
uv run --project frc-docs sphinx-build -T -b gettext $MAINPROJECT/source locale/pot

# Update .tx/config
rm .tx/config
uvx sphinx-intl create-txconfig
echo "lang_map = ${LANG_MAP}" >> .tx/config
uvx sphinx-intl update-txconfig-resources -p locale/pot -d locale --transifex-project-name $MAINPROJECT --transifex-organization-name $ORGANIZATION

# Push and pull from Transifex. It is important to push then pull!
# If you pull then push, the PO files will contain out of date strings.
if [ "$CI" = true ]
then
    tx push --source --skip
fi
tx pull -l $LANG_TO_PULL --mode onlyreviewed --use-git-timestamps
