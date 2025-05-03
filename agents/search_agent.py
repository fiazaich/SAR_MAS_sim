from agents.base_agent import BaseAgent
import random
import json
import os

class SearchAgent(BaseAgent):
    def __init__(self, agent_id, ontology_slice, logger=None, tick_rate=1):
        super().__init__(agent_id, ontology_slice, logger, tick_rate)
        self.location       = "Z0_0"
        self.assigned_zones = []
        self.assigned_zones = []
        self.last_zone_index = -1
        self.proposal_log = []

    def assign_zones(self, zones):
        self.assigned_zones = zones
        if zones:
           self.location = zones[0]          # start inside first zone
            # publish initial pos
           self.memory.validate_and_update(f"AgentPos@{self.agent_id}", "0,0", context={"tick": 0})

    def sample_survivor_status(self):
        distribution = {"detected": 0.3, "none": 0.7}
        options, weights = zip(*distribution.items())
        chosen = random.choices(options, weights=weights, k=1)[0]
        return distribution, chosen

    async def tick(self, agents, tick):
        if tick % self.tick_rate != 0:
            return

        if not self.assigned_zones:
            return

        # Cycle through assigned zones in round-robin fashion
        self.last_zone_index = (self.last_zone_index + 1) % len(self.assigned_zones)
        zone = self.assigned_zones[self.last_zone_index]
        if self.location != zone:
            self.location = zone
            self.memory.validate_and_update(f"AgentPos@{self.agent_id}", f"{zone.split('_')[0][1:]},{zone.split('_')[1]}", context={"tick": tick})

        survivor_key = f"Survivor@{zone}"
        zone_status_key = f"ZoneStatus@{zone}"

        # --- Probabilistic proposal ---
        distribution, chosen = self.sample_survivor_status()
        self.proposal_log.append({
            "tick": tick,
            "zone": zone,
            "distribution": distribution,
            "chosen": chosen
        })

        # Validate and update then broadcast
        if self.memory.validate_and_update(survivor_key, chosen, context={"tick": tick, "agent_id": self.agent_id}):
            self.global_store.add(survivor_key, chosen, tick, self.agent_id)

            await self.broadcast(agents, survivor_key, chosen, tick)
            if self.logger:
                await self.logger.log(tick, self.agent_id, "found_survivor", survivor_key, chosen)

        if self.memory.validate_and_update(zone_status_key, "searched", context={"tick": tick, "agent_id": self.agent_id}):
            await self.broadcast(agents, zone_status_key, "searched", tick)
            if self.logger:
                await self.logger.log(tick, self.agent_id, "zone_status", zone_status_key, "searched")

    def dump_proposals(self, output_dir="logs"):
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"proposals_{self.agent_id}.json")
        with open(path, "w") as f:
            json.dump(self.proposal_log, f, indent=2)
