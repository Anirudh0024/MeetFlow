#!/usr/bin/env bash

set -o errexit

echo "Checking Python version..."
python --version

echo "Checking FFmpeg..."
ffmpeg -version

echo "Checking Node.js..."
node --version

echo "Installing MeetFlow dependencies..."
uv sync --locked --no-install-project

echo "Build completed successfully!"