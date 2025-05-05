import json

agent_id = "search1"
tick = -1  # final tick

with open("logs/local_memories.json") as f:
    local_snapshots = json.load(f)

with open("logs/global_memories_tracker.json") as f:
    global_snapshots = json.load(f)

local = local_snapshots[agent_id][tick]
projected = global_snapshots[agent_id][tick]

mismatches = {
    k: (local.get(k, "<missing>"), projected[k])
    for k in projected
    if local.get(k) != projected[k]
}

print(f"\n{agent_id} has {len(mismatches)} mismatches at final tick:\n")
for k, (have, want) in list(mismatches.items())[:20]:  # show up to 20
    print(f"❌ {k:<30} have={have:<15} expected={want}")
