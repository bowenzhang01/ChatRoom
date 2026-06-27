#!/bin/bash
# Buildozer wrapper with PyPI mirror for WSL
# Use: source this file or run: bash build_with_mirror.sh
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
echo "Using PyPI mirror: $PIP_INDEX_URL"
buildozer android debug
