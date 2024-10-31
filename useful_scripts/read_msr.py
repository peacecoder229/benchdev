#!/usr/bin/env python3
import glob
import os
import sys
import struct

pat="/dev/cpu/*/msr"
paths = glob.glob(pat)
msr = int(sys.argv[1], 16)

for p in paths:
    #fd = open(p, "r")
    f = open(p, os.O_RDONLY)
    os.lseek(f, msr, 0)
    #val = os.read(f, 8)
    #val = val.hex()
    val = struct.unpack('Q', os.read(f, 8))[0]
    #print(val)
    close(f)
    print("MSR %x value is %x" %(msr, val))


