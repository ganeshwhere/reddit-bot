import random
import string

def generate_id():
    key_length = 10
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(key_length))

def generate_bot_id():
    key_length = 7
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(key_length))