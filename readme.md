
# Semantic Fusion Simulation Artifact

## Overview
This repository contains the reference implementation for the Semantic Fusion simulation 
used in the paper "**[Semantic Fusion: Verifiable Alignment in Decentralized Multi-Agent Systems](https://arxiv.org/abs/2601.12580)**".

## Requirements
- Python 3.9 or higher
- See requirements.txt

## Quickstart
1. **Run the simulation**:  
   ```bash
   cd SAR_MAS_sim
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

### Automated alignment-tail experiment
- Instead of running `tools/mem_converge.py` manually for each delivery probability, use `tools/alignment_tail_with_fits.py` to launch the runs and plot the survival curves with exponential fits. Example:
  ```bash
  python tools/alignment_tail_with_fits.py \
    --sim rho0.2:0.2 \
    --sim rho0.5:0.5 \
    --sim rho0.8:0.8 \
    --ticks 100 \
    --output alignment_tail_with_fits.pdf
  ```
- Each `--sim LABEL:COMM_PROB` call rewrites `config/run_mode.json`, runs the sim, saves the logs under `logs/alignment_runs/LABEL/`, and then restores your config. You can also reuse existing runs with `--run LABEL:/path/to/dir`.

### Injecting invalid updates
- Set `bad_update.interval` in `config/run_mode.json` to a positive integer to inject an invalid update every N ticks.  
- Alternatively, list exact tick numbers under `bad_update.ticks` to target specific rounds.  
- You can also override these settings via CLI with `python -m main --bad_interval 5` or `python -m main --bad_ticks 8 17`.

### Scoped delivery (prefix-indexed push)
- During startup the runner builds a prefix → subscribers map from each agent’s ontology slice, and `BaseAgent.broadcast` only iterates receivers whose slice contains the key.  
- Candidate logs are emitted only for those scoped receivers, so communication metrics track the true number of semantic refreshes rather than full-network broadcasts.

### Synthetic fan-out analysis
- To reproduce the Θ(d) slice-scaling experiment, run `python tools/slice_scaling_keys.py`.  
- The script samples random slice assignments for each fan-out fraction and plots the expected message cost along with the ideal and broadcast baselines.  
- Runtime scoped-delivery logs still include `fanout` entries (one per broadcast) if you want to inspect a specific run, but the published figure uses the synthetic study for consistency with the theory.

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
This codebase is released under the [MIT License](LICENSE).

## Citation
If you use this artifact or build on the Semantic Fusion simulator, please cite:

> Sofiya Zaichyk. *Semantic Fusion: Verifiable Alignment in Decentralized Multi-Agent Systems*. 2025.

BibTeX:
```bibtex
@misc{zaichyk2026semanticfusionverifiablealignment,
      title={Semantic Fusion: Verifiable Alignment in Decentralized Multi-Agent Systems}, 
      author={Sofiya Zaichyk},
      year={2026},
      eprint={2601.12580},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2601.12580}, 
}
```
