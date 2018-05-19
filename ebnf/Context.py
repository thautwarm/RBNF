class Context:
    def __init__(self):
        self._local = {}
        self._global = {}

    def __contains__(self, item):
        return item in self._local

    def __getitem__(self, k):
        return self._local[k]

    def __setitem__(self, key, value):
        self._local[key] = value

    @property
    def local(self):
        return self._local

    @property
    def glob(self):
        return self._global

    def copy(self):
        ctx = Context.__new__(Context)
        ctx._local = {}
        ctx._global = self._global
        return ctx

    def __str__(self):
        return f'{{LOCAL: {self._local}| GLOBAL: {self._global}}}'
