import asyncio
import random
import os
import json

COMM_PROB = 1.0        # overwritten by runner at startup


class BaseAgent:
    def __init__(self, agent_id, ontology_slice, logger=None, tick_rate=1):
        self.agent_id = agent_id
        self.memory = None
        self.slice = ontology_slice
        self.logger = logger
        self.tick_rate = tick_rate

    def attach_memory(self, memory):
        self.memory = memory

    def set_global_store(self, store):
        self.global_store = store

    async def receive_message(self, key, value, context):
        if self.memory:
            context = context or {}
            context.setdefault('agent_id', self.agent_id)
            await self.logger.log(context.get('tick', -1), self.agent_id, 'receive', key, value, '-', self.slice.is_in_scope(key)) if self.logger else None
            self.memory.update_from_message(key, value, context)

    def prepare_broadcast(self, key, value, tick):
        return (key, value, {"tick": tick, "agent_id": self.agent_id})

    async def broadcast(self, agents, key, value, tick):
        message = self.prepare_broadcast(key, value, tick)

        for agent in agents:
            if agent.agent_id == self.agent_id:
                continue

            # 1️⃣ Does this update intersect the receiver’s slice?
            in_scope = agent.memory.slice.is_in_scope(key)

            # 2️⃣ Delivery succeeds with probability COMM_PROB iff in scope
            delivered = False
            if in_scope and random.random() < COMM_PROB:
                delivered = True
                await agent.receive_message(*message)

            # 3️⃣ Emit a *candidate* log for every potential refresh
            if self.logger:
                await self.logger.log(
                    tick,                     # same column order as elsewhere
                    agent.agent_id,           # receiver
                    'candidate',              # new event type
                    key,
                    value,
                    str(delivered),           # stored under 'validated' column
                    in_scope                  # stored under 'in_scope' column
                )

    async def tick(self, agents, tick):
        raise NotImplementedError("Subclasses must implement their own tick behavior.")
    
    
