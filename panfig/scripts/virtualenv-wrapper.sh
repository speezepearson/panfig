#!/bin/bash

SCRIPTS_DIR=$(dirname "${BASH_SOURCE[0]}")
PANFIG_DIR=$(dirname "$SCRIPTS_DIR")
python "$PANFIG_DIR" "$@"
