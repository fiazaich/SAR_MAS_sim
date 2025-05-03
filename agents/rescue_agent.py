from agents.base_agent import BaseAgent
import environment.world as gw
import random


class RescueAgent(BaseAgent):
    def __init__(self, agent_id, ontology_slice, logger=None, tick_rate=1):
        super().__init__(agent_id, ontology_slice, logger, tick_rate)
        self.location = random.choice(gw.WORLD.zones)
        self.target_zones = set()
        self.rescued_zones = set()
        self.waiting_for_relay = {}
        self.service_range = (3, 7)    # inclusive bounds – tweak as needed
        self.busy_until: dict[str, int] = {}   

    def move_to(self, zone):
        self.location = zone

    def bid_score(self, zone):
            return -gw.manhattan(self.location, zone) + random.uniform(0, 1e-3)

    async def tick(self, agents, tick):
        if tick % self.tick_rate != 0:
            return

        zones = [k.split("@")[1] for k, v in self.memory.all_state().items()
                 if k.startswith("Survivor@") and v == "detected"
                 and f"Rescue@{k.split('@')[1]}" not in self.memory.all_state()]

        for zone in zones:
            if zone not in self.target_zones and zone not in self.rescued_zones:
                score = self.bid_score(zone)
                bid_key = f"Bid@{zone}"
                bid_val = f"{self.agent_id}:{score:.2f}"
                if self.memory.validate_and_update(bid_key, bid_val, context={"tick": tick, "agent_id": self.agent_id}):
                    self.global_store.add(bid_key, bid_val, tick, self.agent_id)

                    await self.broadcast(agents, bid_key, bid_val, tick)
                    self.target_zones.add(zone)
                    self.waiting_for_relay[zone] = True

        for zone in list(self.target_zones):
            all_bids = [(k, v) for k, v in self.memory.all_state().items()
                        if k == f"Bid@{zone}" and ":" in v]
            highest = max(all_bids, key=lambda x: float(x[1].split(":")[1]), default=None)
            if not highest or highest[1].split(":")[0] != self.agent_id:
                continue

            relay_key = f"Relay@{zone}"
            relay_val = self.memory.get(relay_key)

            if relay_val != "active":
                if self.logger:
                    await self.logger.log(tick, self.agent_id, "wait", relay_key, str(relay_val))
                continue

            if self.location != zone:
                self.move_to(zone)   # publishes AgentPos internally
                c = gw.WORLD.coord(zone)
                self.memory.validate_and_update(f"AgentPos@{self.agent_id}", f"{c.x},{c.y}", context={"tick": tick})
                if self.logger:
                    await self.logger.log(tick, self.agent_id, "move", f"Relocate@{zone}", "moving")

            if zone not in self.busy_until:
                duration = random.randint(*self.service_range)
                self.busy_until[zone] = tick + duration
                if self.logger:
                    await self.logger.log(tick, self.agent_id,
                                          "start_rescue", f"Rescue@{zone}",
                                          f"T={duration}")
                # do *not* complete rescue yet
                continue

            # Still busy? wait.
            if tick < self.busy_until[zone]:
                continue
            rescue_key = f"Rescue@{zone}"
            if self.memory.get(rescue_key) is None:
                if self.memory.validate_and_update(rescue_key, f"by_{self.agent_id}", context={"tick": tick, "agent_id": self.agent_id}):
                    self.global_store.add(rescue_key, f"by_{self.agent_id}", tick, self.agent_id)

                    await self.broadcast(agents, rescue_key, f"by_{self.agent_id}", tick)
                    if self.logger:
                        await self.logger.log(tick, self.agent_id, "rescue", rescue_key, f"by_{self.agent_id}")
                    self.rescued_zones.add(zone)
                    self.target_zones.remove(zone)
                    if zone in self.waiting_for_relay:
                        del self.waiting_for_relay[zone]
                    zone_status_key = f"ZoneStatus@{zone}"
                    if self.memory.validate_and_update(zone_status_key, "unsearched", context={"tick": tick, "agent_id": self.agent_id}):
                        self.global_store.add(zone_status_key, "unsearched",
                                              tick, self.agent_id)
                        await self.broadcast(agents, zone_status_key, "unsearched", tick)
                        if self.logger:
                            await self.logger.log(tick, self.agent_id,
                                                  "zone_reset", zone_status_key, "unsearched")
                        self.busy_until.pop(zone, None)
