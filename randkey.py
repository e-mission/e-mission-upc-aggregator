from __future__ import print_function
import numpy as np
import sys

UMAX_64 = int (np.power (2.0, 64))

KEYSIZE = 256

def random_64s (count):
    val = 0
    for i in range (count):
        val <<= 64
        val += int (np.random.randint (low=0, high=UMAX_64, dtype="uint64"))
    return val

if __name__ == "__main__":
  with open (sys.argv[1], "w") as f:
    key = random_64s (KEYSIZE // 64)
    for i in range (KEYSIZE // 8):
      print ("{}".format (chr (key & 255)), file=f, end="")
      key = key >> 8;
