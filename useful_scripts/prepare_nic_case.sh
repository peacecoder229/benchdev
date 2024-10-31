#!/bin/bash
service irqbalance stop
/pnpdata/set_nic_affinity.py -i enp179s0f0:0,1,2,3+enp179s0f1:4,5,6,7+enp179s0f2:0,1,2,3+enp179s0f3:4,5,6,7 -c 28
/pnpdata/change_msr_percore.py 0x774 0x1212 write
/pnpdata/change_msr_percore.py 0x774 0x1a1a 0-7 write
