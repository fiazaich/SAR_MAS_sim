#!/usr/bin/env python3
"""
Generate per-key alignment delay survival curves with exponential fits
across multiple simulation runs.

Usage:
    python tools/alignment_tail_with_fits.py \
        --run rho0.2:logs/run_rho02 \
        --run rho0.5:logs/run_rho05 \
        --run rho0.8:logs/run_rho08

Each run directory must contain `update_log.csv` and `local_memories.json`.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import rcParams, rc


def export_figure(filename: str):
    rcParams["figure.figsize"] = (3.33, 2.2)
    rcParams["figure.dpi"] = 100
    rcParams["pdf.fonttype"] = 42
    rc("font", family="serif")
    rc("mathtext", fontset="cm")
    plt.savefig(filename, bbox_inches="tight")


def reconstruct_global_trace(update_log: pd.DataFrame) -> List[Dict[str, str]]:
    validated = update_log[
        (update_log["event"] == "memory_update")
        & (update_log["validated"].astype(str).str.upper() == "TRUE")
    ].copy()
    validated["tick"] = validated["tick"].astype(int)
    max_tick = validated["tick"].max()

    trace: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for t in range(max_tick + 1):
        tick_updates = validated[validated["tick"] == t]
        for _, row in tick_updates.iterrows():
            current[row["key"]] = row["value"]
        trace.append(current.copy())
    return trace


def load_alignment_delays(run_dir: str) -> List[int]:
    update_path = os.path.join(run_dir, "update_log.csv")
    local_path = os.path.join(run_dir, "local_memories.json")

    if not (os.path.exists(update_path) and os.path.exists(local_path)):
        raise FileNotFoundError(
            f"Expected update_log.csv and local_memories.json in {run_dir}"
        )

    update_log = pd.read_csv(update_path)
    with open(local_path) as f:
        local_memories = json.load(f)

    global_trace = reconstruct_global_trace(update_log)
    T = len(global_trace)
    alignment_delays: List[int] = []

    for t in range(T - 1):
        g_prev = global_trace[t]
        g_next = global_trace[t + 1]
        for key in g_next:
            if key not in g_prev or g_next[key] != g_prev[key]:
                for agent, mem_list in local_memories.items():
                    if len(mem_list) <= t + 1 or key not in mem_list[t + 1]:
                        continue
                    if mem_list[t + 1].get(key) == g_next[key]:
                        continue

                    for t_prime in range(t + 2, T):
                        if len(mem_list) <= t_prime:
                            break
                        local_val = mem_list[t_prime].get(key)
                        global_val = global_trace[t_prime].get(key)
                        if local_val == global_val:
                            alignment_delays.append(t_prime - (t + 1))
                            break
    return alignment_delays


def compute_survival(delays: List[int]) -> Tuple[np.ndarray, np.ndarray]:
    if not delays:
        return np.array([]), np.array([])
    xs = np.array(sorted(set(delays)))
    ys = np.array([np.mean([d > x for d in delays]) for x in xs])
    return xs, ys


def main():
    parser = argparse.ArgumentParser(
        description="Plot alignment-delay survival curves with exponential fits."
    )
    parser.add_argument(
        "--run",
        action="append",
        metavar="LABEL:RUN_DIR",
        help="Run label and directory containing update_log/local_memories.",
    )
    parser.add_argument(
        "--sim",
        action="append",
        metavar="LABEL:COMM_PROB",
        help="Launch a simulation with the specified comm_prob and capture its logs.",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=100,
        help="Tick count to use when launching simulations (default: 100).",
    )
    parser.add_argument(
        "--config",
        default="config/run_mode.json",
        help="Simulation config file to edit when launching runs.",
    )
    parser.add_argument(
        "--log_base",
        default="logs/alignment_runs",
        help="Base directory where auto-run logs should be stored.",
    )
    parser.add_argument(
        "--output",
        default="alignment_tail_with_fits.pdf",
        help="Path to output PDF.",
    )
    args = parser.parse_args()

    run_specs = list(args.run or [])

    if args.sim:
        with open(args.config) as f:
            original_cfg = json.load(f)
        os.makedirs(args.log_base, exist_ok=True)
        try:
            for spec in args.sim:
                try:
                    label, prob_str = spec.split(":", 1)
                except ValueError:
                    raise SystemExit(f"Invalid --sim '{spec}', expected LABEL:COMM_PROB")
                comm_prob = float(prob_str)
                cfg = dict(original_cfg)
                cfg["comm_prob"] = comm_prob
                with open(args.config, "w") as f:
                    json.dump(cfg, f, indent=2)

                print(f"[RUN] {label}: comm_prob={comm_prob}, ticks={args.ticks}")
                subprocess.run(
                    [sys.executable, "-m", "main", "--ticks", str(args.ticks)],
                    check=True,
                )
                dest = os.path.join(args.log_base, label)
                os.makedirs(dest, exist_ok=True)
                shutil.copy("logs/update_log.csv", os.path.join(dest, "update_log.csv"))
                shutil.copy(
                    "logs/local_memories.json",
                    os.path.join(dest, "local_memories.json"),
                )
                run_specs.append(f"{label}:{dest}")
        finally:
            with open(args.config, "w") as f:
                json.dump(original_cfg, f, indent=2)

    if not run_specs:
        raise SystemExit("Please supply --run LABEL:DIR or use --sim to launch runs.")

    plt.style.use("seaborn-v0_8-paper")
    plt.rc("font", family="serif", size=10)
    plt.rc("mathtext", fontset="dejavuserif")
    plt.rc("axes", titlesize=14, labelsize=11)
    plt.rc("xtick", labelsize=10)
    plt.rc("ytick", labelsize=10)
    plt.rc("legend", fontsize=9)
    plt.figure(figsize=(5.5, 3.0))

    summary_rows = []
    for spec in run_specs:
        try:
            label, run_dir = spec.split(":", 1)
        except ValueError:
            raise SystemExit(f"Invalid --run specification '{spec}' (expected LABEL:DIR)")

        delays = load_alignment_delays(run_dir)
        xs, ys = compute_survival(delays)
        if xs.size == 0:
            print(f"[WARN] No alignment delays for {label}")
            continue

        lam = 1.0 / np.mean(delays) if delays else 0.0
        fit_x = np.linspace(0, xs.max(), 200)
        fit_y = np.exp(-lam * fit_x)

        plt.semilogy(xs, ys, marker="o", linestyle="-", label=f"{label} empirical")
        plt.semilogy(fit_x, fit_y, linestyle="--", label=f"{label} fit ($\\lambda={lam:.3f}$)")

        summary_rows.append(
            {
                "label": label,
                "mean_delay": float(np.mean(delays)),
                "median_delay": float(np.median(delays)),
                "max_delay": int(np.max(delays)),
                "lambda_hat": float(lam),
                "num_samples": len(delays),
            }
        )

    plt.xlabel("Delay threshold $k$ (ticks)")
    plt.ylabel("$S(k) = \\Pr[\\Delta > k]$")
    plt.title("Alignment Delay Tails with Exponential Fits")
    plt.grid(True, which="both", axis="y")
    plt.tight_layout()
    plt.legend()
    export_figure(args.output)
    print(f"[✓] Plot written to {args.output}")

    if summary_rows:
        df = pd.DataFrame(summary_rows)
        summary_path = os.path.splitext(args.output)[0] + "_summary.csv"
        df.to_csv(summary_path, index=False)
        print(f"[✓] Summary metrics written to {summary_path}")


if __name__ == "__main__":
    main()
