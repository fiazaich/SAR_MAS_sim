import json
import os
import pandas as pd

# === CONFIG ===
LOG_PATH = "logs/update_log.csv"
LOCAL_MEMORIES_PATH = "logs/local_memories.json"
GLOBAL_TRACE_PATH = "reconstructed_global_memory_trace_corrected.json"
ONTOLOGY_ACCESS_PATH = "logs/ontology_access.json"

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

with open(GLOBAL_TRACE_PATH, "w") as f:
    json.dump(memory_trace, f, indent=2)

print(f"[✓] Global memory trace reconstructed: {GLOBAL_TRACE_PATH}")

# === THEOREM 1: Semantic Coherence ===
def check_global_semantic_coherence(global_trace, allowed_prefixes):
    violations = []
    total_checked = 0
    for t, memory in enumerate(global_trace):
        for key, value in memory.items():
            total_checked += 1
            prefix = key.split("@")[0] if "@" in key else None
            if prefix not in allowed_prefixes:
                violations.append((t, key, value))
    return violations, total_checked

# === THEOREM 3: Causal Isolation (only new keys per step) ===
def check_causal_isolation(local_memories, slice_prefixes):
    violations = []
    total_checked = 0
    for agent, memory_list in local_memories.items():
        allowed = slice_prefixes.get(agent, [])
        prev_keys = set()
        for t, mem in enumerate(memory_list):
            current_keys = set(mem.keys())
            new_keys = current_keys - prev_keys
            for key in new_keys:
                total_checked += 1
                if not any(key.startswith(prefix + "@") for prefix in allowed):
                    violations.append((agent, t, key))
            prev_keys = current_keys
    return violations, total_checked


if __name__ == "__main__":
    # Load inputs
    with open(GLOBAL_TRACE_PATH) as f:
        global_trace = json.load(f)

    with open(LOCAL_MEMORIES_PATH) as f:
        local_memories = json.load(f)

    with open(ONTOLOGY_ACCESS_PATH) as f:
        slice_prefixes = json.load(f)
    print(f"# agents: {len(local_memories)}")
    print(f"# steps per agent: {[len(mem) for mem in local_memories.values()][:3]}  # sample")
    print(f"# avg keys per snapshot (agent 0): {[len(m) for m in list(local_memories.values())[0]][:5]}  # first 5")


    # Extract full set of ontology prefixes from all agents
    all_allowed_prefixes = set()
    for prefixes in slice_prefixes.values():
        all_allowed_prefixes.update(prefixes)

    print("\n[✓] Checking Theorem 1: Semantic Coherence")
    t1_violations, t1_total = check_global_semantic_coherence(global_trace, all_allowed_prefixes)
    print(f"Total violations: {len(t1_violations)} / {t1_total}")

    if t1_violations:
        print("Sample:", t1_violations[:5])

    print("\n[✓] Checking Theorem 3: Causal Isolation")
    t3_violations, t3_total = check_causal_isolation(local_memories, slice_prefixes)
    print(f"Total violations: {len(t3_violations)} / {t3_total}")

    if t3_violations:
        print("Sample:", t3_violations[:5])
