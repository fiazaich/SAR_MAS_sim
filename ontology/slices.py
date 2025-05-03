from ontology.ontology import Ontology

class OntologySlice:
    def __init__(self, allowed_prefixes):
        self.allowed_prefixes = allowed_prefixes  # e.g., ["Survivor", "Rescue"]
        self.ontology = Ontology()

    def is_in_scope(self, key):
        base = key.split("@")[0]
        return base in self.allowed_prefixes

    def validates(self, key, value):
        return self.is_in_scope(key) and self.ontology.is_valid_key(key) and self.ontology.is_valid_value(key, value)
