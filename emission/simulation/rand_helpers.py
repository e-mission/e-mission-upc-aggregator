import numpy as np

UMAX_64 = int (np.power (2.0, 64))

def random_64s (count):
    val = 0
    for i in range (count):
        val <<= 64
        val += int (np.random.randint (low=0, high=UMAX_64, dtype="uint64"))
    return val

def gen_random_key ():
    return random_64s (4)

def gen_random_key_string ():
    return str (random_64s (4))

def gen_random_email ():
    return gen_random_key_string () + "@emission-test"
