#!/usr/bin/env python3
import os
import sys
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from simulation.runner import generate_fanout_slices

# === CONFIGURATION ===
FRACTIONS = [0.05, 0.20, 0.40, 0.60, 0.80, 1.0]
RUNS      = 100                           # repetitions per fraction
KEYS      = ["Survivor", "ZoneStatus", "Relay", "Rescue", "Bid"]
# =====================

plt.style.use('seaborn-v0_8-paper')
plt.rc('font',      family='serif', size=10)
plt.rc('mathtext',  fontset='dejavuserif')
plt.rc('axes',      titlesize=14, labelsize=11)
plt.rc('xtick',     labelsize=10)
plt.rc('ytick',     labelsize=10)
plt.rc('legend',    fontsize=9)

from matplotlib import rcParams, rc

def export_figure(filename="slice_scaling.pdf"):
    # Physical size: fits 3.33-inch IEEE column
    rcParams["figure.figsize"] = (3.33, 2.2)   # width, height in inches
    rcParams["figure.dpi"] = 100               # dpi irrelevant for PDF
    rcParams["pdf.fonttype"] = 42              # embed TrueType
    rc("font", family="serif")                 # Computer Modern
    rc("mathtext", fontset="cm")
    plt.savefig(filename, bbox_inches="tight") # vector, loss-free


def measure():
    """
    Returns (data, total_agents)
      data          = [(f, mean_msgs, std_msgs), …]
      total_agents  = rescue + relay (used for the ideal/broadcast lines)
    """
    data = []
    total_agents = None                   # we’ll discover this on the first run

    for f in FRACTIONS:
        all_counts = []

        for seed in range(RUNS):
            # build slices
            _, rescue_slices, relay_slices = generate_fanout_slices(f, seed)

            # record the total once
            if total_agents is None:
                total_agents = len(rescue_slices) + len(relay_slices)

            # 1 publisher (search-agent) per key
            subs = {k: 1 for k in KEYS}

            # bump counts for every subscribing agent
            for sl in (rescue_slices + relay_slices):
                for k in sl.allowed_prefixes:
                    if k in subs:         # ignore AgentPos / ZoneCoord
                        subs[k] += 1

            all_counts.extend(subs.values())

        data.append((f, np.mean(all_counts), np.std(all_counts)))

    return data, total_agents


def plot(data, total_agents):
    f_vals = np.linspace(0, 1, 100)

    fs, means, stds = zip(*data)
    means, stds = np.asarray(means), np.asarray(stds)

    # asym­metric whiskers: never dip below 1 msg
    lower_err = np.minimum(stds, means - 1.0)
    upper_err = stds

    plt.figure()
    plt.errorbar(fs, means,
                 yerr=[lower_err, upper_err],
                 fmt="o-", capsize=3,
                 label="measured avg msgs")

    plt.plot(f_vals, f_vals * total_agents + 1, "--",
             label=f"ideal: f·{total_agents}+1")

    plt.axhline(total_agents + 1, linestyle=":", color="gray",
                label=f"broadcast: {total_agents+1} msgs")

    plt.xlabel("Slice fraction $f$")
    plt.ylabel("Avg. messages per update")
    plt.title("Θ(d) Scaling by Semantic Overlap")
    plt.legend()
    plt.tight_layout()
    
    export_figure("convergence.pdf")

    


if __name__ == "__main__":
    data, N_agents = measure()
    plot(data, N_agents)
