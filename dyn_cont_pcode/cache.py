class Cache(object):
    Content = {}

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(Cache, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def set(self, key, value):
        self.Content[key] = value

    def get(self, key):
        if key not in self.Content.keys():
            return None
        return self.Content[key]


class CacheTransCode:
    strategy = "ST"
    strategy_conf = "STTG"
    workload = "WL"
    workload_conf = "WLCF"
