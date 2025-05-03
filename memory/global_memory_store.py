import os
import json
from collections import defaultdict

class GlobalMemoryStore:
    def __init__(self, ontology_access_path):
        with open(ontology_access_path, "r") as f:
            self.ontology_access = json.load(f)
        self.memory = {}  # Global memory key-value store
        self.snapshots = defaultdict(list)  # Per-agent memory projections

    def add(self, key, value, tick, agent_id=None):
        # Store the latest global value
        self.memory[key] = value

    def snapshot(self, agents, tick):
        # Project global memory for each agent and store it
        for agent in agents:
            allowed = self.ontology_access.get(agent.agent_id, [])
            projected = {
                k: v for k, v in self.memory.items()
                if k.split("@")[0] in allowed
            }
            self.snapshots[agent.agent_id].append(projected)

    def save(self, out_path="logs/global_memories.json"):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(self.snapshots, f, indent=2)
