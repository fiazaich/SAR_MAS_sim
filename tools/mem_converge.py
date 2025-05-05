import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams, rc
import os

cfg = json.load(open("config/run_mode.json"))

# === CONFIG ===
LOG_PATH = "logs/update_log.csv"
LOCAL_MEMORIES_PATH = "logs/local_memories.json"
OUTPUT_TRACE_PATH = "reconstructed_global_memory_trace_corrected.json"
PLOT_PATH = "alignment_delay_tail_fixed.pdf"
CSV_OUTPUT = "alignment_delays.csv"
COMM_PROB = cfg.get("comm_prob", 1.0)

def export_figure(filename="convergence.pdf"):
    # Physical size: fits 3.33-inch IEEE column
    rcParams["figure.figsize"] = (3.33, 2.2)   # width, height in inches
    rcParams["figure.dpi"] = 100               # dpi irrelevant for PDF
    rcParams["pdf.fonttype"] = 42              # embed TrueType
    rc("font", family="serif")                 # Computer Modern
    rc("mathtext", fontset="cm")
    plt.savefig(filename, bbox_inches="tight") 

# === STEP 1: Reconstruct Global Memory Trace ===
update_log = pd.read_csv(LOG_PATH)

validated = update_log[
    (update_log["event"] == "memory_update") &
    (update_log["validated"].astype(str).str.upper() == "TRUE")
]

validated["tick"] = validated["tick"].astype(int)
max_tick = validated["tick"].max()

memory_trace = []
current_memory = {}

for t in range(max_tick + 1):
    tick_updates = validated[validated["tick"] == t]
    for _, row in tick_updates.iterrows():
        current_memory[row["key"]] = row["value"]
    memory_trace.append(current_memory.copy())

with open(OUTPUT_TRACE_PATH, "w") as f:
    json.dump(memory_trace, f, indent=2)

print(f"[✓] Global memory trace reconstructed: {OUTPUT_TRACE_PATH}")

# === STEP 2: Load Local Agent Memories ===
with open(LOCAL_MEMORIES_PATH) as f:
    local_memories = json.load(f)

# === STEP 3: Compute Alignment Delays ===
T = len(memory_trace)
alignment_delays = []

for t in range(T - 1):
    g_prev = memory_trace[t]
    g_next = memory_trace[t + 1]

    for key in g_next:
        if key not in g_prev or g_next[key] != g_prev[key]:
            for agent, mem_list in local_memories.items():
                if len(mem_list) <= t + 1 or key not in mem_list[t + 1]:
                    continue
                if mem_list[t + 1][key] == g_next[key]:
                    continue

                # Search for alignment
                for t_prime in range(t + 2, T):
                    if len(mem_list) <= t_prime:
                        break
                    local_val = mem_list[t_prime].get(key)
                    global_val = memory_trace[t_prime].get(key)
                    if local_val == global_val:
                        alignment_delays.append((agent, key, t + 1, t_prime - (t + 1)))
                        break
                else:
                    alignment_delays.append((agent, key, t + 1, None))

# === STEP 4: Analyze and Plot ===
delays = [d for (_, _, _, d) in alignment_delays if d is not None]
xs = np.array(sorted(set(delays)))
ys = np.array([np.mean([d > x for d in delays]) for x in xs])

plt.style.use('seaborn-v0_8-paper')
plt.rc('font',      family='serif', size=10)
plt.rc('mathtext',  fontset='dejavuserif')
plt.rc('axes',      titlesize=14, labelsize=11)
plt.rc('xtick',     labelsize=10)
plt.rc('ytick',     labelsize=10)
plt.rc('legend',    fontsize=9)
plt.figure(figsize=(8, 5))
plt.semilogy(xs, ys, marker='o', linestyle='-', label="Empirical tail")
plt.xlabel("Delay threshold d (ticks)")
plt.ylabel("Pr(alignment delay > d)")
plt.title("Per-Key Alignment Delay Tail (Semilog-y)")
plt.grid(True, which='both', axis='y')
plt.tight_layout()
plt.legend()
export_figure(PLOT_PATH)
#plt.savefig(PLOT_PATH, dpi=300)

print(f"[✓] Tail plot saved: {PLOT_PATH}")

# === STEP 5: Save CSV of Delays ===
comm_prob = COMM_PROB  # change this per run
CSV_OUTPUT = f"alignment_delays_cp{comm_prob}.csv"
df_out = pd.DataFrame(alignment_delays, columns=["agent", "key", "global_tick", "delay"])
df_out.to_csv(CSV_OUTPUT, index=False)


print(f"[✓] Alignment delays written to: {CSV_OUTPUT}")

# === STEP 6: Summary ===
summary = {
    "mean_delay": np.mean(delays) if delays else None,
    "median_delay": np.median(delays) if delays else None,
    "max_delay": np.max(delays) if delays else None,
    "min_delay": np.min(delays) if delays else None,
    "num_aligned": len(delays),
    "num_total": len(alignment_delays),
    "num_failed": len(alignment_delays) - len(delays)
}

print("[✓] Alignment Summary:")
for k, v in summary.items():
    print(f"  {k}: {v}")

# === STEP 7: Save summary row to persistent results CSV ===  # <-- set this manually per run
summary_row = {"comm_prob": comm_prob, **summary}

results_path = "alignment_summary.csv"
csv_exists = os.path.isfile(results_path)

with open(results_path, "a", newline="") as f:
    writer = pd.DataFrame([summary_row])
    if not csv_exists:
        writer.to_csv(f, index=False, header=True)
    else:
        writer.to_csv(f, index=False, header=False)

print(f"[✓] Summary appended to: {results_path}")

