import asyncio
import os
import json
import argparse
import math, random
from collections import defaultdict
from ontology.slices import OntologySlice
from memory.memory_store import LocalMemory
from memory.global_memory_store import GlobalMemoryStore
from agents import base_agent
from agents.search_agent import SearchAgent
from agents.rescue_agent import RescueAgent
from agents.relay_agent import RelayAgent
from logger.logger import Logger
from tools.theorem_validator import MemorySnapshotTracker
from environment.world import GridWorld, set_world

cfg = json.load(open("config/run_mode.json"))
# tracker = None
# global_store = GlobalMemoryStore("tools/ontology_access.json")
global_store = None   # placeholder so name exists at module scope
tracker       = None
GRID_W, GRID_H = cfg.get("world_w", 10), cfg.get("world_h", 10)          # tweak in config later
WORLD = GridWorld(GRID_W, GRID_H)
ONTO_PATH = os.path.join("logs", "ontology_access.json")
set_world(WORLD)
N_SEARCH = cfg.get("n_search", 10)
N_RESCUE = cfg.get("n_rescue", 10)
N_RELAY = cfg.get("n_relay", 40)
TICKS = cfg.get("duration", 100)

def generate_fanout_slices(fan_out: float, seed: int = 42):
    """
    Returns (search_slice, rescue_slices, relay_slices).
    fan_out in [0,1] controls fraction of agents that see each prefix.
    """
    PREFIXES = ["Survivor", "ZoneStatus", "Relay", "Rescue", "Bid"]
    COMMON = {"ZoneCoord", "AgentPos"}  
    rng = random.Random(seed)

    # Search always sees the two prefixes
    search_slice = OntologySlice(["Survivor", "ZoneStatus", *COMMON])

    # Prepare per‑agent prefix sets
    N_search = N_SEARCH
    N_rescue = N_RESCUE
    N_relay  = N_RELAY
    total    = N_rescue + N_relay
    k        = max(1, round(fan_out * total))
    print(f"[DEBUG] fan_out={fan_out:.2f} -> k={k} owners of 40")


    rescue_allowed = [set() for _ in range(N_rescue)]
    relay_allowed  = [set() for _ in range(N_relay)]

    for p in PREFIXES:
        owners = rng.sample(range(total), k)
        for idx in owners:
            if idx < N_rescue:
                rescue_allowed[idx].add(p)
            else:
                relay_allowed[idx - N_rescue].add(p)

             # <-- add once here

    search_slices = [search_slice] * N_search
    rescue_slices = [
        OntologySlice(sorted((s or {"Survivor"}) | COMMON))
        for s in rescue_allowed
    ]
    relay_slices  = [
        OntologySlice(sorted((s or {"Survivor"}) | COMMON))
        for s in relay_allowed
    ]
    return search_slices, rescue_slices, relay_slices


def build_delivery_map(agents):
    mapping = defaultdict(list)
    for agent in agents:
        for prefix in agent.slice.allowed_prefixes:
            mapping[prefix].append(agent)
    return mapping


def inject_bad_update(all_agents, tick, rng=None):
    """
    Force a randomly selected agent to attempt an invalid memory update.
    Validator should reject these updates, allowing us to assert correctness.
    """
    if not all_agents:
        return False

    rng = rng or random
    agent = rng.choice(all_agents)
    invalid_prefix = rng.choice(["Forbidden", "Corrupted", "InvalidKey"])
    key = f"{invalid_prefix}@tick{tick}"
    value = f"bad_payload_{rng.randint(1000, 9999)}"
    context = {"tick": tick, "agent_id": agent.agent_id, "event": "bad_update"}

    print(f"[INJECTION] {agent.agent_id} attempting invalid update {key}={value}")
    return agent.memory.validate_and_update(key, value, context=context)

async def main():
    global global_store, tracker
    logger = Logger(log_dir=os.path.join(os.path.dirname(__file__), "..", "logs"))

    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks",   type=int,   default=100)
    parser.add_argument("--fan_out", type=float, default=None,
                        help="Fraction of agents to share each prefix (0–1).")
    parser.add_argument("--drop", action="store_true", default=True,
                        help="Enable failure injection at tick 6 (default: true).")
    parser.add_argument("--bad_interval", type=int, default=None,
                        help="Inject a bad update every N ticks (0/None disables).")
    parser.add_argument("--bad_ticks", type=int, nargs="*", default=None,
                        help="Specific ticks that should receive a bad update injection.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Override RNG seed (default from config).")
    args = parser.parse_args()
    cfg = json.load(open("config/run_mode.json"))
    print(f"[DEBUG] loaded config: {cfg}")
    fan_out = args.fan_out if args.fan_out is not None else cfg.get("fan_out", None)
    seed    = args.seed if args.seed is not None else cfg.get("seed",  42)
    comm_prob = cfg.get("comm_prob", 1.0) 
    base_agent.COMM_PROB = comm_prob
    ticks = args.ticks or TICKS
    bad_update_cfg = cfg.get("bad_update", {})
    cfg_interval = int(bad_update_cfg.get("interval", 0) or 0)
    cfg_ticks = bad_update_cfg.get("ticks", [])
    if isinstance(cfg_ticks, int):
        cfg_ticks = [cfg_ticks]
    elif not isinstance(cfg_ticks, (list, tuple, set)):
        cfg_ticks = []
    bad_update_interval = cfg_interval if args.bad_interval is None else max(0, args.bad_interval)
    bad_update_ticks = cfg_ticks if args.bad_ticks is None else args.bad_ticks
    bad_update_ticks = {int(t) for t in bad_update_ticks if t is not None}

    #add zones from gridworld
    
    # Set RNG seed for reproducibility
    random.seed(seed)
    if fan_out == 1.0:
        # correctness mode: one slice per role
        
        COMMON = ["ZoneCoord", "AgentPos"]       # new always-allowed prefixes
        print("no fan")
        search_slice = OntologySlice(["Survivor", "ZoneStatus", *COMMON])
        rescue_slice = OntologySlice(["Survivor", "Rescue", "Bid", "Relay", *COMMON])
        relay_slice  = OntologySlice(["Survivor", "Rescue", "Relay", *COMMON])

        # same slice for every agent of that role
        search_slices = [search_slice] * N_SEARCH
        rescue_slices = [rescue_slice] * N_RESCUE
        relay_slices  = [relay_slice]  * N_RELAY
    else:
        # experimental fan‑out mode
        print(f"[INFO] fan_out={fan_out}, seed={seed}")
        search_slices, rescue_slices, relay_slices = generate_fanout_slices(fan_out, seed=seed)
        from collections import Counter

        # rescue_slices and relay_slices are lists of OntologySlice
        all_allowed = [p for sl in (rescue_slices + relay_slices) for p in sl.allowed_prefixes]
        coverage = Counter(all_allowed)
        #print(f"[DEBUG SLICE] f={fan_out:.2f} slice coverage:", coverage)

    search_agents = [SearchAgent(f"search{i+1}", search_slices[i], logger)
                     for i in range(N_SEARCH)]
    rescue_agents = [RescueAgent(f"rescue{i+1}", rescue_slices[i], logger)
                     for i in range(N_RESCUE)]
    relay_agents  = [RelayAgent (f"relay{i+1}", relay_slices[i],  logger)
                     for i in range(N_RELAY)]
    all_agents    = search_agents + rescue_agents + relay_agents
    base_agent.BaseAgent.register_delivery_map(build_delivery_map(all_agents))
    
    access_map = {
        agent.agent_id: sorted(agent.slice.allowed_prefixes)
        for agent in all_agents
}
    
    os.makedirs("logs", exist_ok=True)
    with open(ONTO_PATH, "w") as f:
        json.dump(access_map, f, indent=2)
    
    global_store = GlobalMemoryStore(ONTO_PATH)
    tracker       = MemorySnapshotTracker(ONTO_PATH)
    

    # Zones to cover
    zone_list = WORLD.zones.copy()
    random.shuffle(zone_list)

    # Attach memory
    all_agents = search_agents + rescue_agents + relay_agents
    for agent in all_agents:
        agent.attach_memory(LocalMemory(agent.slice, logger, agent_id=agent.agent_id))
        agent.set_global_store(global_store)
    print(len(all_agents))

    for zone in WORLD.zones:
        c = WORLD.coord(zone)
        key = f"ZoneCoord@{zone}"
        val = f"{c.x},{c.y}"
        global_store.add(key, val, 0, "system")
        for agent in all_agents:
            if agent.slice.is_in_scope(key):
                agent.memory.validate_and_update(key, val, context={"tick": 0, "agent_id": "system"})

        if logger:                               # emit to CSV so we can verify
            await logger.log(0, "system", "seed", key, val)

    # Distribute zones across search agents
    zones_per_agent = math.ceil(len(zone_list) / len(search_agents))
    for i, agent in enumerate(search_agents):
        assigned = zone_list[i*zones_per_agent : (i+1)*zones_per_agent]
        agent.assign_zones(assigned)

    for tick in range(1, ticks + 1):
        print(f"\n--- TICK {tick} ---")
        if tick == 6:
            print("Simulating failure: rescue2 and relay1 disabled.")
            for agent in rescue_agents + relay_agents:
                if agent.agent_id in {"rescue2", "relay1"}:
                    async def noop(*args, **kwargs):
                        pass
                    agent.tick = noop  # Disable the agent
                    if agent.logger:
                        await agent.logger.log(tick, agent.agent_id, "failure", "status", "agent_offline", validated=False, in_scope=True)

        should_inject_bad = False
        if bad_update_interval and bad_update_interval > 0 and tick % bad_update_interval == 0:
            should_inject_bad = True
        if tick in bad_update_ticks:
            should_inject_bad = True
        if should_inject_bad:
            inject_bad_update(all_agents, tick, rng=random)

        await asyncio.gather(*(agent.tick(all_agents, tick) for agent in all_agents))
        # Snapshot memory after all updates
        combined_global = {}
        for a in all_agents:
            combined_global.update(a.memory.all_state())
        tracker.snapshot(all_agents, combined_global)
        global_store.snapshot(all_agents, tick)

    for agent in all_agents:
        agent.tick = lambda *_: None  # disable behavior

    for flush_tick in range(1, 11):
        print(f"\n--- FLUSH TICK {flush_tick} ---")
        # no new updates — just snapshot
        combined_global = {}
        for a in all_agents:
            combined_global.update(a.memory.all_state())
        tracker.snapshot(all_agents, combined_global)
        global_store.snapshot(all_agents, flush_tick)



    for agent in all_agents:
        if agent.memory:
            logger.register_memory(agent.agent_id, agent.memory.all_state())

    # Step: Generate ontology_access.json for evaluation
    ontology_access = {
        agent.agent_id: list(agent.slice.allowed_prefixes)
        for agent in all_agents
    }
    with open(os.path.join(logger.log_dir, "ontology_access.json"), "w") as f:
        json.dump(ontology_access, f, indent=2)

    global_store.save("logs/global_memories_canonical.json")
    # Save true final global memory (used by convergence checker)
    # with open("logs/memory_dump_global.json", "w") as f:
    #     json.dump(global_store.memory, f, indent=2)
    combined_global = global_store.memory
    tracker.snapshot(all_agents, combined_global)

    logger.dump()
    tracker.save("logs")
    for agent in search_agents:
        agent.dump_proposals("logs")

if __name__ == "__main__":
    asyncio.run(main())
