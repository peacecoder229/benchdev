#os mailbox acess 
import os
import commands
import sys 

import osmailbox_access as mbox

def hwdrc_reg_dump(dummy_data,socket):
    print "==hwdrc register dump=="
    print "MCLOS_EN"
    mbox.mbox_read(hwdrc_reg['MCLOS_EN']('r'))
    
    print "CLOSToMEMCLOS"
    mbox.mbox_read(hwdrc_reg['CLOSToMEMCLOS']('r'))

    print "MCLOS0"
    mbox.mbox_read(hwdrc_reg['MCLOS0']('r'))

    print "MCLOS1"
    mbox.mbox_read(hwdrc_reg['MCLOS1']('r'))

    print "MCLOS2"
    mbox.mbox_read(hwdrc_reg['MCLOS2']('r'))

    print "MCLOS3"
    mbox.mbox_read(hwdrc_reg['MCLOS3']('r'))

    print "CONFIG0"
    mbox.mbox_read(hwdrc_reg['CONFIG0']('r'))

def hwdrc_init_to_default(data,socket):
    print "write to CLOSToMEMCLOS,map 0-3,8-15,CLOS4-MCLOS 0(HP) ,CLOS 5-MCLOS 1, CLOS6- MCLOS 2, CLOS7-MCLOS3(LP)"
    mbox.mbox_write(hwdrc_reg['CLOSToMEMCLOS']('w'),0x0000E400)

    print "write to MCLOS0,memCLOS 0(HP) with MAX delay 0x1, MIN delay 0x1, priority 0x0"
    mbox.mbox_write(hwdrc_reg['MCLOS0']('w'),0x00010100)

    print "write to MCLOS1,memCLOS 1, with MAX delay 0xff, MIN delay 0x1, priority 0xF"
    mbox.mbox_write(hwdrc_reg['MCLOS1']('w'),0x00FF010F)

    print "write to MCLOS2,#memCLOS 2, with MAX delay 0xff, MIN delay 0x1, priority 0x3F"
    mbox.mbox_write(hwdrc_reg['MCLOS2']('w'),0x00FF013F)

    print "write to MCLOS3,#memCLOS 3(LP), with MAX delay 0xff, MIN delay 0x1, priority 0xFF"
    mbox.mbox_write(hwdrc_reg['MCLOS3']('w'),0x00ff01ff)

    print "write to CONFIG0,#enable MEM_CLOS_EVEMT #MEM_CLOS_EVENT= 0x80 MCLOS_RPQ_OCCUPANCY_EVENT #MEM_CLOS_TIME_WINDOW=0x01 #MEMCLOS_SET_POINT=0x01"
    mbox.mbox_write(hwdrc_reg['CONFIG0']('w'),0x01800101)

    print "write to MCLOS_EN"
    mbox.mbox_write(hwdrc_reg['MCLOS_EN']('w'),0x00000002)

def invalid_hwdrc_cmd(data,socket):
    print "Invalid_hwdrc_cmd",data,socket
    print "Command format:python hwdrc_config.py function_name data socket"
    print "function_name=[CLOSToMEMCLOS,MCLOS0,MCLOS1,MCLOS2,MCLOS3,CONFIG0,MCLOS_EN,init,reg_dump]"
    print "socket=[0,1]"
    print "Samples:" 
    print "1.init the hwdrc with default config on socket 0"
    print "python hwdrc_config.py init 0x0 0"
    print "2. write hwdrc register  CLOSToMEMCLOS to 0xe400 on socket 0"
    print "python hwdrc_config.py CLOSToMEMCLOS 0x0e400 0"
    sys.exit(1)

def write_CLOSToMEMCLOS(data,socket):
    print "write_CLOSToMEMCLOS",data,socket
    mbox.mbox_write(hwdrc_reg['CLOSToMEMCLOS']('w'),data)

def write_MCLOS0(data,socket):
    print "write_MCLOS0",data,socket
    mbox.mbox_write(hwdrc_reg['MCLOS0']('w'),data)

def write_MCLOS1(data,socket):
    print "write_MCLOS1",data,socket
    mbox.mbox_write(hwdrc_reg['MCLOS1']('w'),data)

def write_MCLOS2(data,socket):
    print "write_MCLOS2",data,socket
    mbox.mbox_write(hwdrc_reg['MCLOS2']('w'),data)

def write_MCLOS3(data,socket):
    print "write_MCLOS3",data,socket
    mbox.mbox_write(hwdrc_reg['MCLOS3']('w'),data)

def write_CONFIG0(data,socket):
    print "write_CONFIG0",data,socket
    mbox.mbox_write(hwdrc_reg['CONFIG0']('w'),data)

def write_MCLOS_EN(data,socket):
    print "write_MCLOS_EN",data,socket
    mbox.mbox_write(hwdrc_reg['MCLOS_EN']('w'),data)


hwdrc_config_entry ={
  'CLOSToMEMCLOS':write_CLOSToMEMCLOS,
  'MCLOS0' : write_MCLOS0,
  'MCLOS1' : write_MCLOS1, 
  'MCLOS2' : write_MCLOS2,
  'MCLOS3' : write_MCLOS3,
  'CONFIG0' : write_CONFIG0,
  'MCLOS_EN' : write_MCLOS_EN,
  'init':hwdrc_init_to_default,
  'reg_dump':hwdrc_reg_dump,
}

hwdrc_reg = {
  'CLOSToMEMCLOS' : lambda write:'0x810001d2' if write=='w' else '0x800001d2',
  'MCLOS0' : lambda write :'0x810002d2' if write=='w' else '0x800002d2',
  'MCLOS1' : lambda write :'0x810102d2' if write=='w' else '0x800102d2',
  'MCLOS2' : lambda write :'0x810202d2' if write=='w' else '0x800202d2',
  'MCLOS3' : lambda write :'0x810302d2' if write=='w' else '0x800302d2',
  'CONFIG0' : lambda write :'0x810003d2' if write=='w' else '0x800003d2',
  'MCLOS_EN' : lambda write :'0x810004d2' if write=='w' else '0x800004d2'
}

if(len(sys.argv)==4):
    hwdrc_config_entry.get(sys.argv[1],invalid_hwdrc_cmd)(sys.argv[2],sys.argv[3]) 
else:
    invalid_hwdrc_cmd(0xED,0)

#print "read"
#mbox.mbox_read(hwdrc_reg['CLOSToMEMCLOS']('r'))

#hwdrc_reg_dump()

#hwdrc_init_to_default()

#hwdrc_reg_dump()

#mbox.mbox_write(hwdrc_reg['CLOSToMEMCLOS']('w'),0x5555AAAA)
#print "read"
#mbox.mbox_read(hwdrc_reg['CLOSToMEMCLOS']('r'))
