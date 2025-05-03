from agents.base_agent import BaseAgent
import random
import environment.world as gw


class RelayAgent(BaseAgent):
    def __init__(self, agent_id, ontology_slice, logger=None, tick_rate=1):
        super().__init__(agent_id, ontology_slice, logger, tick_rate)
        self.location = self.location = random.choice(gw.WORLD.zones)
        self.covered_zones = set()
        self.claimed_zones = set()

    def move_to(self, zone):
        self.location = zone
        if self.logger:
            import asyncio
            asyncio.create_task(self.logger.log(-1, self.agent_id, "move", f"Relocate@{zone}", "moving"))
                # publish updated position
        c = gw.WORLD.coord(zone)
        x, y = c.x, c.y
        self.memory.validate_and_update(f"AgentPos@{self.agent_id}", f"{x},{y}", context={"tick": -1})

    def get_active_claims(self, agents):
        active_claims = {}
        for agent in agents:
            if isinstance(agent, RelayAgent) and agent is not self:
                for zone in agent.claimed_zones:
                    active_claims[zone] = active_claims.get(zone, 0) + 1
        return active_claims

    async def tick(self, agents, tick):
        if tick % self.tick_rate != 0:
            return

        survivor_zones = [k.split("@")[1] for k, v in self.memory.all_state().items()
                          if k.startswith("Survivor@") and v == "detected"]

        active_claims = self.get_active_claims(agents)

        # Preference for zones with fewest other claims
        candidate_zones = [z for z in survivor_zones if z not in self.covered_zones]
        if not candidate_zones:
            return

        # Sort by how many other agents have claimed each zone (ascending)
        candidate_zones.sort(key=lambda z: active_claims.get(z, 0))

        for zone in candidate_zones:
            if zone in self.claimed_zones:
                continue

            self.claimed_zones.add(zone)
            self.move_to(zone)

            relay_key = f"Relay@{zone}"
            success = self.memory.validate_and_update(
                relay_key, "active", context={"tick": tick, "agent_id": self.agent_id}
            )
            if success:
                self.global_store.add(relay_key, "active", tick, self.agent_id)

                await self.broadcast(agents, relay_key, "active", tick)
                if self.logger:
                    await self.logger.log(tick, self.agent_id, "relay", relay_key, "active")
                self.covered_zones.add(zone)

            self.claimed_zones.discard(zone)
            break  # Only move to one zone per tick
