import json 

tail = -1  # last tick
agent = "search1"

# Load files
with open("logs/local_memories.json") as f:
    local = json.load(f)

with open("logs/global_memories_tracker.json") as f:
    global_proj = json.load(f)

# Compare
print(local[agent][tail] == global_proj[agent][tail])
