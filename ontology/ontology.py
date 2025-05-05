import re

class Ontology:
    def __init__(self):
        self.valid_keys = {
            "Survivor": ["detected", "none"],
            "Rescue": ["by_.*"],
            "Relay": ["active"],
            "ZoneStatus": ["searched", "unsearched"],
            "Bid": [r".+?:-?\d+(\.\d+)?"],
            "ZoneCoord": ["\\d+,\\d+"],   # immutable seed
            "AgentPos":  ["\\d+,\\d+"]  
        }

    def is_valid_key(self, key):
        base = key.split("@")[0]
        return base in self.valid_keys

    def is_valid_value(self, key, value):
        base = key.split("@")[0]
        if base not in self.valid_keys:
            return False
        patterns = self.valid_keys[base]
        return any(re.fullmatch(pattern, value) for pattern in patterns)
