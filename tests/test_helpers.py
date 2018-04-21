from configclasses.sources import Source

class DictSource(Source):
    def __init__(self, **kwargs):
        self.canonical_kv_mapping = {**kwargs}
