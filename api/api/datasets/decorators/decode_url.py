from urllib.parse import unquote
from functools import wraps


def decode_url(func):
    @wraps(func)
    def wrapper(cls, url: str, *args, **kwargs):
        decoded_url = unquote(url).replace('+', ' ')
        return func(cls, decoded_url, *args, **kwargs)
    return wrapper
