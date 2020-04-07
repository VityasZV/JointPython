from functools import lru_cache
from urllib.parse import parse_qs, urlparse

__all__ = ['Request', 'Response', 'HTTPError', 'MAX_HEADERS', 'MAX_LINE']

MAX_LINE = 64 * 1024
MAX_HEADERS = 100


class Request:
    def __init__(self, method, target, version, headers, rfile):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile
        self.body = self.get_body()

    @property
    def path(self):
        return self.url.path

    @property
    @lru_cache(maxsize=None)
    def query(self):
        return parse_qs(self.url.query)

    @property
    @lru_cache(maxsize=None)
    def url(self):
        return urlparse(self.target)

    def get_body(self):
        size = self.headers.get('Content-Length')
        if not size:
            return None
        return self.rfile.read(int(size))


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body


class HTTPError(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body
