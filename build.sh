#!/bin/bash

pip install -r requirements.txt pyinstaller==5.9.0 staticx

# Get the Git version hash
git_hash=$(git rev-parse --short HEAD)

# Write the Git version hash to git_version.py
echo "GIT_HASH = '${git_hash}'" > git_version.py

# Build the dynamic executable binary with PyInstaller
python -m PyInstaller --onefile --name twilight_streamer main.py

# Bundle dynamic executables with their library dependencies so they can be run
# anywhere, just like a static executable.

if grep -q 'Raspberry' /proc/cpuinfo || [ -n "$GITHUB_ACTION" ]; then
    echo "This system is a Raspberry Pi or the script is running in a GitHub Actions workflow."
    echo "staticx cannot be run."
else
  echo "GITHUB_ACTION is not present. staticx can be run."
  python -m staticx dist/twilight_streamer dist/twilight_streamer
fi
