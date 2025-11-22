import asyncio
import random
import os
import json

COMM_PROB = 1.0        # overwritten by runner at startup


class BaseAgent:
    PREFIX_SUBSCRIBERS = {}

    @classmethod
    def register_delivery_map(cls, mapping):
        cls.PREFIX_SUBSCRIBERS = mapping or {}

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

    def _scoped_recipients(self, key, agents):
        prefix = key.split("@")[0]
        scoped = self.PREFIX_SUBSCRIBERS.get(prefix)
        if scoped is None:
            return [
                agent for agent in agents
                if agent.agent_id != self.agent_id and agent.memory.slice.is_in_scope(key)
            ]
        return [agent for agent in scoped if agent.agent_id != self.agent_id]

    async def broadcast(self, agents, key, value, tick):
        message = self.prepare_broadcast(key, value, tick)
        recipients = self._scoped_recipients(key, agents)

        if self.logger:
            await self.logger.log(
                tick,
                self.agent_id,
                'fanout',
                key,
                str(len(recipients)),
                True,
                True
            )

        for agent in recipients:
            in_scope = agent.memory.slice.is_in_scope(key)
            delivered = False
            if in_scope and random.random() < COMM_PROB:
                delivered = True
                await agent.receive_message(*message)

            if self.logger:
                await self.logger.log(
                    tick,
                    agent.agent_id,
                    'candidate',
                    key,
                    value,
                    str(delivered),
                    in_scope
                )

    async def tick(self, agents, tick):
        raise NotImplementedError("Subclasses must implement their own tick behavior.")
