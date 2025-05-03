#!/usr/bin/env bash
set -e

echo "1. Running simulation..."
python main.py

echo "2. Checking deterministic properties..."
python logs/theorem_analysis.py

echo "3. Checking bisimulation properties..."
python logs/theorem_validator2.py

echo "All checks passed."