
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
   python -m main
   ```
   This generates logs in the `logs/` directory.

2. **Verify deterministic properties**:  
   ```bash
   python tools/theorem_analysis.py
   ```
   Expect:
   ```
   coherence_score = 1.0
   convergence_score = 1.0
   ```

3. **Verify bisimulation properties**:  
   ```bash
   python tools/theorem_validator.py
   ```
   Expect:
   ```
   score = 1.0  (for both stuttering and probabilistic bisimulation)
   ```

4. **Run all tests**:  
   ```bash
   bash run_all_tests.sh
   ```

5. **Verify Geometric Tail Convergence**:
   For each run to be plotted:
   - set ```comm_prob``` in config/run_mode.json to desired message probability
   - run the sim ```python -m main```
   - run tools/mem_converge.py
   Once all per-comm_prob analyses are run:
   ```bash
   python tools/plot_alignment_tails.py
   ```
   Note: running with higher ```comm_prob``` values induces little or no  message loss and, while the alignment curve is exponential, typically will have points rise above the bound due to violation of the i.i.d. message assumption.

## Directory Structure
- `agents/` – agent implementations 
- `config/` - simulation configuration
- `environment/` - world definition 
- `memory/` – memory store modules  
- `ontology/` – ontology definitions  
- `simulation/` – runner and environment  
- `logger/` – logging utilities  
- `logs/` – output logs and analysis data  
- `tests/` – debugging test scripts
- `tools/` - all analysis and plotting tools   

## License
MIT (or your preferred license)
