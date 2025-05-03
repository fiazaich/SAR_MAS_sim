
class LocalMemory:
    def __init__(self, ontology_slice, logger=None, agent_id=None):
        self.state = {}
        self.slice = ontology_slice
        self.logger = logger
        self.agent_id = agent_id
        self.received_updates = []

    def validate_and_update(self, key, value, context=None):
        in_scope = self.slice.is_in_scope(key)
        validated = self.slice.validates(key, value)
        success = False

        if validated:
            self.state[key] = value
            self.received_updates.append((key, value, context))
            success = True

        if self.logger and context:
            tick = context.get("tick", -1)
            agent = context.get("agent_id", self.agent_id)
            import asyncio
            if asyncio.get_event_loop().is_running():
                asyncio.create_task(self.logger.log(tick, agent, "memory_update", key, value, validated, in_scope))
            else:
                # fallback sync log if outside async context
                import threading
                threading.Thread(target=self.logger.log, args=(tick, agent, "memory_update", key, value, validated, in_scope)).start()

        return success

    def get(self, key):
        return self.state.get(key)

    def all_state(self):
        return self.state.copy()

    def update_from_message(self, key, value, context=None):
        return self.validate_and_update(key, value, context)
