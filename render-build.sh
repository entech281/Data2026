#!/bin/bash
# Build script for Render deployment
# This is not strictly necessary since render.yaml handles it,
# but can be used if you prefer a separate build script

set -e

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

echo "Installing dependencies..."
uv sync --frozen

echo "Initializing database schema..."
uv run python -m frc_data_281.db

echo "Syncing TBA data..."
uv run python -m frc_data_281.the_blue_alliance.pipeline

echo "Build complete!"
