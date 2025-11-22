#!/usr/bin/env bash
set -e

echo "1. Running simulation with bad-update injection..."
python3 main.py --bad_ticks 5

echo "2. Checking deterministic properties..."
python3 tools/theorem_analysis.py

echo "3. Checking bisimulation properties..."
python3 tools/theorem_validator.py

echo "4. Checking convergence properties..."
python3 tools/slice_scaling_keys.py --output slice_scaling_ci.pdf
