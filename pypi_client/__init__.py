from appdirs import user_cache_dir
from diskcache import Cache

cache = Cache(user_cache_dir('pypi-client', 'PyPI'))
