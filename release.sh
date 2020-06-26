#!/bin/sh

set -ex

copy frc-docs/.tx/config .tx/config
tx pull -l fr_CA,es_MX --mode onlyreviewed --use-git-timestamps