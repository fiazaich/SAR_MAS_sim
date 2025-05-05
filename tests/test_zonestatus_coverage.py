import json

key_to_check = "Bid@Z4_1"

with open("logs/global_memories_tracker.json") as f:
    global_proj = json.load(f)
with open("logs/ontology_access.json") as f:
    ontology = json.load(f)

# Step 1: find the first tick when the key appears in any projection
tick0 = None
for t in range(len(next(iter(global_proj.values())))):
    for agent in global_proj:
        if key_to_check in global_proj[agent][t]:
            tick0 = t
            break
    if tick0 is not None:
        break

if tick0 is None:
    print(f"❌ {key_to_check} never appeared in global snapshots.")
else:
    print(f"🔍 Key {key_to_check} first appeared at tick {tick0}")
    print("Who saw it:")
    for agent in sorted(global_proj):
        if key_to_check in global_proj[agent][tick0]:
            slice = ontology[agent]
            print(f"  {agent:10} — has it, slice = {slice}")

