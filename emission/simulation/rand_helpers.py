import numpy as np

UMAX_16 = int (np.power (2.0, 16))

def random_16s (count):
    val = 0
    for i in range (count):
        val <<= 16
        val += int (np.random.randint (low=0, high=UMAX_16, dtype="uint64"))
    return val

def gen_random_key ():
    return random_16s (4)

def gen_random_key_string ():
    return str (random_16s (4))

def gen_random_email ():
    return gen_random_key_string () + "@emission-test"
