import random
import string

def random_token(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
