#!/bin/bash

HERE=$(dirname "${BASH_SOURCE[0]}")
python "$(dirname "$HERE")/__main__.py" "$@"
