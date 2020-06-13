class _Cache:
	def __init__(self):
		self._cache = {}

	def get(self, key):
		if key not in self._cache: return None
		return self._cache[key]

	def set(self, key, value):
		self._cache[key] = value

CompletedJobsCache = _Cache()