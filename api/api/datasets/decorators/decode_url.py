import urllib.parse
from functools import wraps


def decode_url(func):
    @wraps(func)
    def wrapper(cls, url: str, *args, **kwargs):
        parsed_url = urllib.parse.urlparse(url)
        decoded_path = urllib.parse.unquote(parsed_url.path)
        decoded_query = urllib.parse.unquote_plus(parsed_url.query)
        decoded_url = parsed_url._replace(path=decoded_path, query=decoded_query).geturl()
        return func(cls, decoded_url, *args, **kwargs)
    return wrapper
