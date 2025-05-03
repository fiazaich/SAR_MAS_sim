
# Semantic Fusion Simulation Artifact

## Overview
This repository contains the reference implementation for the Semantic Fusion simulation 
used in the paper "Scoped Semantic Reasoning in Decentralized Agents: A Formal Framework and Reference Architecture".

## Requirements
- Python 3.9 or higher
- No external packages required; all dependencies are in the Python standard library.

## Quickstart
1. **Run the simulation**:  
   ```bash
   cd working_rescue_sim_v4
   python main.py
   ```
   This generates logs in the `logs/` directory.

2. **Verify deterministic properties**:  
   ```bash
   python logs/theorem_analysis.py
   ```
   Expect:
   ```
   coherence_score = 1.0
   convergence_score = 1.0
   isolation_score = 1.0
   ```

3. **Verify bisimulation properties**:  
   ```bash
   python logs/theorem_validator2.py
   ```
   Expect:
   ```
   score = 1.0  (for both stuttering and probabilistic bisimulation)
   ```

4. **Run all tests**:  
   ```bash
   bash run_all_tests.sh
   ```

## Directory Structure
- `agents/` – agent implementations  
- `memory/` – memory store modules  
- `ontology/` – ontology definitions  
- `simulation/` – runner and environment  
- `logger/` – logging utilities  
- `logs/` – output logs and analysis data  
- `tests/` – placeholder for future unit tests  

## License
MIT (or your preferred license)
