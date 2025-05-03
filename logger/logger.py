import os
import csv
import json
from datetime import datetime


class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, "update_log.csv")
        self.memory_dumps = []
        self.theorem_results = []

        # Initialize CSV file
        with open(self.log_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["tick", "agent", "time", "event", "key", "value", "validated", "in_scope"])

    async def log(self, tick, agent, event, key, value, validated=True, in_scope=True):
        with open(self.log_path, "a", newline="") as csvfile:
            timestamp = datetime.now().isoformat()
            writer = csv.writer(csvfile)
            writer.writerow([tick, agent, timestamp, event, key, value, validated, in_scope])

    def register_memory(self, agent_id, memory_dict):
        self.memory_dumps.append((agent_id, memory_dict))

    def register_theorem_result(self, result_dict):
        self.theorem_results.append(result_dict)

    def dump(self):
        os.makedirs(self.log_dir, exist_ok=True)

        for agent_id, memory_dict in self.memory_dumps:
            file_path = os.path.join(self.log_dir, f"memory_dump_{agent_id}.json")
            with open(file_path, "w") as f:
                json.dump(memory_dict, f, indent=2)

        if self.theorem_results:
            result_path = os.path.join(self.log_dir, "theorem_log.json")
            with open(result_path, "w") as f:
                json.dump(self.theorem_results, f, indent=2)

    # logger.py  ➜  new helper
    def emit_candidate(tick, agent, key, in_scope, delivered):
        _write({
            "tick": tick,
            "agent": agent,
            "event": "candidate",   # potential refresh for this agent
            "key": key,
            "in_scope": in_scope,   # True / False
            "delivered": delivered  # True if refresh actually arrived
        })

