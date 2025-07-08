#!/bin/bash
source /home/291928k/miniconda3/etc/profile.d/conda.sh
conda activate mining_analytics
poetry run python -c "import asyncio; from src.cli import demo; asyncio.run(demo())"
