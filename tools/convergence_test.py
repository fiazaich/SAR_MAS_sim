import pandas as pd, sys, collections, math
import pandas as pd, collections, math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, rc

def export_figure(filename="convergence.pdf"):
    # Physical size: fits 3.33-inch IEEE column
    rcParams["figure.figsize"] = (3.33, 2.2)   # width, height in inches
    rcParams["figure.dpi"] = 100               # dpi irrelevant for PDF
    rcParams["pdf.fonttype"] = 42              # embed TrueType
    rc("font", family="serif")                 # Computer Modern
    rc("mathtext", fontset="cm")
    plt.savefig(filename, bbox_inches="tight") # vector, loss-free


def convergence_metrics(csv_path, rho=0.05, eta=0.05):
    df = pd.read_csv(csv_path)

    # 1. commits that *create* new semantic facts
    commits       = df[df.event == "memory_update"].copy()
    commits["kv"] = commits.key + "=" + commits.value

    # 2. refreshes that *deliver* them
    receives       = df[df.event == "receive"].copy()
    receives["kv"] = receives.key + "=" + receives.value

        # ---- empirical  η̂  (slice-hit probability) -----------------------------
    # ------------------------------------------------------------------------
# Parameter estimation for Theorem 18
# ------------------------------------------------------------------------
    num_agents = df.agent.nunique()

    # 1) ρ̂  —  delivery-success probability
    candidates = df[(df.event == "candidate") & (df.in_scope)]
    rho_hat    = len(receives) / max(len(candidates), 1)        # successes / trials

    # 2) η̂  —  slice-hit probability (only commits that CAN propagate)
    deliverable_prefix = ('Survivor', 'ZoneStatus', 'RelayReady')
    scoped_commits     = commits[commits.key.str.startswith(deliverable_prefix)]

    hits = (receives
            .groupby(['kv', 'tick']).agent.nunique()
            .reindex(scoped_commits.set_index(['kv', 'tick']).index,
                    fill_value=0))

    eta_hat = ((hits - 1).clip(lower=0)).mean() / (num_agents - 1)

    # 3) λ̂  —  frequency of deliverable commits per tick
    ticks_with_commits = scoped_commits.tick.nunique()
    total_ticks        = df.tick.max() - df.tick.min() + 1
    lambda_hat         = ticks_with_commits / total_ticks

    # 4) Per-tick success probability p̂
    p_hat = rho_hat * eta_hat * lambda_hat
    print(f"ρ̂={rho_hat:.4f},   η̂={eta_hat:.4f},   λ̂={lambda_hat:.4f},   "
        f"ρ̂η̂λ̂ (p̂)={p_hat:.4e}")

    # 3. earliest receive tick per (agent, kv)
    first_seen = {}
    for _, r in receives.iterrows():
        first_seen.setdefault((r.agent, r.kv), r.tick)

    # 4. first-arrival delays
    delays_by_agent = collections.defaultdict(list)
    agents          = df.agent.unique()

    for _, c in commits.iterrows():
        ct, kv = c.tick, c.kv
        for agent in agents:
            t_first = first_seen.get((agent, kv))
            if t_first is not None and t_first >= ct:
                delays_by_agent[agent].append(t_first - ct)

    flat = [d for lst in delays_by_agent.values() for d in lst]

    if not flat:                       # nothing to analyse
        print("No first-arrival data found."); return

    print(f"  average receivers per scoped commit  : {hits.mean():.2f}")
    print(f"  after removing author                : {(hits-1).mean():.2f}")
    print(f"  η̂ (=fraction of agents)             : {eta_hat:.4f}")


    # 5. summary
    print(f"unique (agent,kv) arrivals ……… {len(flat):,}")
    print(f"mean first-arrival delay  …… {sum(flat)/len(flat):.1f} ticks")
    print(f"max  first-arrival delay   …… {max(flat)} ticks")

    # 6. survival curve vs. theorem bound
    kmax = max(flat)
    ks   = np.arange(kmax+1)
    Sk_emp = [sum(d > k for d in flat)/len(flat) for k in ks]
    bound  = [(1 - rho*eta)**k for k in ks]

    print(f"\n[DEBUG] Delay stats:")
    print(f"Total delays recorded: {len(flat)}")
    print(f"Delay histogram: {collections.Counter(flat)}")
    print(f"Max delay: {max(flat) if flat else 'N/A'}")


    plt.style.use('seaborn-v0_8-paper')
    plt.rc('font',      family='serif', size=10)
    plt.rc('mathtext',  fontset='dejavuserif')
    plt.rc('axes',      titlesize=14, labelsize=11)
    plt.rc('xtick',     labelsize=10)
    plt.rc('ytick',     labelsize=10)
    plt.rc('legend',    fontsize=9)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    ax.set_title(r"Geometric-tail convergence")
    ax.step(ks, Sk_emp, where="post", label=r"empirical $S(k)$", linewidth=1.2)
    ax.plot(ks, bound, "--", label=r"$(1-\hat\rho\hat\eta\hat\lambda)^k$ bound", color='darkorange', linewidth=1.5)

    ax.set_yscale("log")
    ax.set_xlabel(r"$k$")
    ax.set_ylabel(r"Survival $S(k)$")

    ax.set_xlim(0, 300)
    ax.set_ylim(1e-3, 1.1)  # pad slightly above 1 for aesthetics

    ax.grid(True, which="both", linestyle=":", linewidth=0.5, alpha=0.7)
    ax.legend(loc="lower left", frameon=False)
    fig.tight_layout()
    fig.savefig("geometric_tail_convergence.png", dpi=300, bbox_inches="tight")
    export_figure("convergence.pdf")
    plt.show()

    return flat, delays_by_agent



if __name__ == "__main__":
    convergence_metrics(sys.argv[1])

