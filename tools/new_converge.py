import pandas as pd, sys, collections, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, rc
import os

def agent_slice_convergence(csv_path, ontology_path="logs/ontology_access.json"):
    df = pd.read_csv(csv_path)
    df["kv"] = df.key + "=" + df.value

    # Load ontology slice definitions
    with open(ontology_path, "r") as f:
        ontology_access = json.load(f)

    # Track the last commit tick for each committed key=value
    memory_updates = df[df.event == "memory_update"]
    latest_tick_by_kv = {
        f"{row.key}={row.value}": row.tick
        for _, row in memory_updates.iterrows()
    }

    # Track: agent → kv → first time it was received (at or after commit)
    receives = df[df.event == "receive"]
    received_by_agent = collections.defaultdict(dict)

    for _, row in receives.iterrows():
        kv = row.kv
        commit_tick = latest_tick_by_kv.get(kv)
        if commit_tick is not None and row.tick >= commit_tick:
            agent_log = received_by_agent[row.agent]
            agent_log[kv] = min(row.tick, agent_log.get(kv, float("inf")))

    # Compute per-agent convergence
    convergence_ticks = {}
    for agent, slice_prefixes in ontology_access.items():
        # All committed kvs relevant to this agent's slice
        final_slice_kvs = {
            kv for kv in latest_tick_by_kv
            if kv.split("@")[0] in slice_prefixes
        }
        print(f"[{agent}] total slice prefixes: {slice_prefixes}")
        print(f"[{agent}] committed slice kvs: {len(final_slice_kvs)}")


        # What this agent actually received
        received_kvs = set(received_by_agent.get(agent, {}).keys())

        if final_slice_kvs.issubset(received_kvs):
            convergence_ticks[agent] = max(
                received_by_agent[agent][kv] for kv in final_slice_kvs
            )
        else:
            convergence_ticks[agent] = None

        # Debug print
        print(f"[{agent}] received {len(received_kvs & final_slice_kvs)} / {len(final_slice_kvs)} slice kvs")

    # Extract convergence ticks
    converged_ticks = [t for t in convergence_ticks.values() if t is not None]
    if not converged_ticks:
        print("❌ No agents fully converged on their slice.")
        return

    kmax = max(converged_ticks)
    ks = np.arange(kmax + 1)
    survival = [sum(t > k for t in converged_ticks) / len(converged_ticks) for k in ks]

    # Plot
    plt.style.use("seaborn-v0_8-paper")
    rcParams["figure.figsize"] = (3.33, 2.2)
    rcParams["pdf.fonttype"] = 42
    rc("font", family="serif")
    rc("mathtext", fontset="cm")

    fig, ax = plt.subplots()
    ax.set_title("Agent Slice Convergence")
    ax.step(ks, survival, where="post", label="empirical $S(k)$", linewidth=1.2)
    ax.set_yscale("log")
    ax.set_xlabel("Tick $k$")
    ax.set_ylabel("Fraction of agents not yet converged")
    ax.set_xlim(0, min(300, kmax + 10))
    ax.set_ylim(1e-3, 1.1)
    ax.grid(True, which="both", linestyle=":", linewidth=0.5, alpha=0.7)
    ax.legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig("agent_slice_convergence.png", dpi=300, bbox_inches="tight")
    plt.show()

    return convergence_ticks

if __name__ == "__main__":
    agent_slice_convergence(sys.argv[1])
