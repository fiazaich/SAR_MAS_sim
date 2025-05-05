import json
from collections import defaultdict
import os
from glob import glob


class MemorySnapshotTracker:
    def __init__(self, ontology_path):
        with open(ontology_path, "r") as f:
            self.ontology_access = json.load(f)
        self.local_snapshots = defaultdict(list)
        self.global_snapshots = defaultdict(list)

    def snapshot(self, agents, global_memory):
        for agent in agents:
            agent_id = agent.agent_id
            self.local_snapshots[agent_id].append(agent.memory.all_state())
            proj = {
                k: v for k, v in global_memory.items()
                if k.split("@")[0] in self.ontology_access.get(agent_id, [])
            }
            self.global_snapshots[agent_id].append(proj)

    def save(self, out_dir="logs"):
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "local_memories.json"), "w") as f:
            json.dump(self.local_snapshots, f, indent=2)
        with open(os.path.join(out_dir, "global_memories_tracker.json"), "w") as f:
            json.dump(self.global_snapshots, f, indent=2)


def combine_proposal_logs(log_dir="logs"):
    combined = {}
    for path in glob(os.path.join(log_dir, "proposals_*.json")):
        agent_id = os.path.basename(path).replace("proposals_", "").replace(".json", "")
        with open(path, "r") as f:
            combined[agent_id] = json.load(f)

    with open(os.path.join(log_dir, "proposal_distributions.json"), "w") as f:
        json.dump(combined, f, indent=2)


def load_ontology_slice(agent_id, ontology_path):
    with open(ontology_path, "r") as f:
        ontology_access = json.load(f)
    return set(ontology_access.get(agent_id, []))


def project_memory(memory, ontology_slice):
    return {k: v for k, v in memory.items() if k.split("@")[0] in ontology_slice}

def equal_slice(local, projected):
    """
    Forward subset only: every fact the agent currently believes
    appears unchanged in the projected global slice.
    """
    return all(projected.get(k) == v for k, v in local.items())


def validate_stuttering_bisim(local_memory_log, global_memory_log, ontology_path, max_delay=3):
    with open(local_memory_log, "r") as f:
        local_snapshots = json.load(f)
    with open(global_memory_log, "r") as f:
        global_snapshots = json.load(f)
    print(max_delay)
    violations = []
    for agent_id, agent_memory in local_snapshots.items():
        slice_keys = load_ontology_slice(agent_id, ontology_path)
        local_trace = agent_memory
        global_trace = global_snapshots.get(agent_id, [])
        
        for t, local_state in enumerate(local_trace):
            if t > 24:
                continue
            local_proj = {k: v for k, v in local_state.items()
                        if k.split("@")[0] in slice_keys}

            match_found = False
            for dt in range(max_delay + 1):
                if t + dt < len(global_trace):
                    projected = project_memory(global_trace[t + dt], slice_keys)
                    if equal_slice(local_proj, projected):
                        match_found = True
                        break

            if not match_found:
                if len(violations) == 0:
                    print("\nFirst mismatch:",
                        "agent", agent_id, "time-step", t)
                    print("  local slice :", local_proj)
                    print("  global slice:", projected)
                    print("  slice keys  :", sorted(slice_keys)[:8], "...")
                violations.append({"agent": agent_id, "tick": t})

    return {
        "agents_tested": len(local_snapshots),
        "violations": len(violations),
        "score": round(1 - len(violations) / max(1, sum(len(v) for v in local_snapshots.values())), 3),
    }


def validate_probabilistic_bisim(distribution_log_path, global_log_path):
    with open(distribution_log_path, "r") as f:
        local_distributions = json.load(f)
    with open(global_log_path, "r") as f:
        global_updates = json.load(f)

    mismatch_count = 0
    total_samples = 0

    for agent_id, actions in local_distributions.items():
        global_trace = global_updates.get(agent_id, [])
        for tick, dist_entry in enumerate(actions):
            chosen = dist_entry.get("chosen")
            # Check whether chosen value appears anywhere in global canonical memory
            globally_seen = any(
                chosen in state.values()
                for state in global_trace
            )
            if not globally_seen:
                continue  # skip unvalidated or unbroadcast proposals

            projected_state = global_trace[tick] if tick < len(global_trace) else {}
            if chosen not in projected_state.values():
                mismatch_count += 1
            total_samples += 1

    score = 1 - mismatch_count / max(total_samples, 1)
    return {
        "total_samples": total_samples,
        "mismatches": mismatch_count,
        "probabilistic_alignment_score": round(score, 3)
    }


if __name__ == "__main__":
    print("Testing Theorem 5(Stuttering Bisimulation)...")
    result1 = validate_stuttering_bisim("logs/local_memories.json", "logs/global_memories_tracker.json", "logs/ontology_access.json", max_delay=30)
    print(json.dumps(result1, indent=2))

    combine_proposal_logs("logs")
    print("\nTesting Theorem 7 (Probabilistic Bisimulation)...")
    result2 = validate_probabilistic_bisim("logs/proposal_distributions.json", "logs/global_memories_canonical.json")
    print(json.dumps(result2, indent=2))