#!/usr/bin/env bash
set -e

echo "1. Running simulation..."
python main.py

echo "2. Checking deterministic properties..."
python tools/theorem_analysis.py

echo "3. Checking bisimulation properties..."
python tools/theorem_validator.py

echo "4. Checking convergence properties..."
python tools/slice_scaling_key.py
