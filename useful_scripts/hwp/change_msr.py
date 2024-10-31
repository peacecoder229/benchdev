#!/usr/bin/env python
import os
import glob
import struct
import sys

def writemsr(msr, val, core=-1):
    if (core == -1):
      if (os.path.exists("/dev/cpu/cpu0/msr")):
        n = glob.glob('/dev/cpu/cpu*/msr')
      elif (os.path.exists("/dev/cpu/0/msr")):
        n = glob.glob('/dev/cpu/*/msr')
      else:
        print_msr_error(core=-1)
        return
    else:
      # different versions of linux use different cpu naming conventions
      if (os.path.exists("/dev/cpu/cpu%d/msr"%core)):
        n = glob.glob("/dev/cpu/cpu%d/msr"%core)
      elif (os.path.exists('/dev/cpu/0/msr')):
        n = glob.glob("/dev/cpu/%d/msr"%core)
      else:
        print_msr_error(core=core)
        return
    for c in n:
        try:
          f = os.open(c, os.O_WRONLY)
        except:
          print "Could not open file %s"%f
          print " - The MSR kernel module may not be loaded.  Try to install with \"modprobe msr\" as root"
          return
        os.lseek(f, msr, 0)
        #os.lseek(f, msr, os.SEEK_SET) # seek set does not always work
        os.write(f, struct.pack('Q', val))
        print "%24s | MSR(0x%x) = 0x%x"%(c, msr, val)
        os.close(f)

def readmsr(msr):
    if (os.path.exists("/dev/cpu/cpu0/msr")):
      n = glob.glob('/dev/cpu/cpu*/msr')
    elif (os.path.exists("/dev/cpu/0/msr")):
      n = glob.glob('/dev/cpu/*/msr')
    else:
      print_msr_error(core=-1)
      return -1
    vals = []
    for c in n:
        f = os.open(c, os.O_RDONLY)
        #os.lseek(f, msr, os.SEEK_SET) # SEEK_SET does not always work
        os.lseek(f, msr, 0)
        val = struct.unpack('Q', os.read(f, 8))[0]
        print "%24s | 0x%8x | %16d | %s"%(c, val, val, bin(val))
        os.close(f)
    return val

tot = len(sys.argv) - 1 

if sys.argv[tot] == "read":
	print "%x" % (readmsr(int(sys.argv[1], 16)),)
elif sys.argv[tot] == "write": 
	writemsr(int(sys.argv[1], 16), int(sys.argv[2], 16))
	print "%x" % (readmsr(int(sys.argv[1], 16)),)
else:

	print "Usage: "
        print " msr read to read values"
	print " msr newval write  to write"


	

	writemsr(int(sys.argv[1], 16), int(sys.argv[2], 16))
	
