#os mailbox acess 
#import msr_access
import os
import commands
import time
import sys 

import const

def mbox_busy():
    busy_count=0
    mbox_is_busy=True
    while True:
        busy_count+=1
        mboxif=commands.getoutput("rdmsr ""-p 1 "+const.MSR_OS_MAILBOX_INTERFACE)
        mbox_is_busy=((int(mboxif,32) & const.MBOX_INTERFACE_RUN_BUSY) == const.MBOX_INTERFACE_RUN_BUSY)
        if (mbox_is_busy and (busy_count< 50)):
            print "mbox interface runbusy=1, wait 20ms, then retry"
            time.sleep(0.02)#sleep 20ms, if the is busy
            contine
        else:
            break

    return mbox_is_busy

def mbox_busy_Socket1():
    busy_count=0
    mbox_is_busy=True
    while True:
        busy_count+=1
        mboxif=commands.getoutput("rdmsr ""-p 25 "+const.MSR_OS_MAILBOX_INTERFACE)
        mbox_is_busy=((int(mboxif,32) & const.MBOX_INTERFACE_RUN_BUSY) == const.MBOX_INTERFACE_RUN_BUSY)
        if (mbox_is_busy and (busy_count< 50)):
            print "mbox interface runbusy=1, wait 20ms, then retry"
            time.sleep(0.02)#sleep 20ms, if the is busy
            contine
        else:
            break

    return mbox_is_busy

def mbox_write_data_interface(interface,data):
    
    if(mbox_busy()):
        print "mbox_is_busy not recover after 50 retry"
        sys.exit(1)
    os.system("wrmsr ""-p 1 "+const.MSR_OS_MAILBOX_DATA+" "+str(data))
    os.system("wrmsr ""-p 1 "+const.MSR_OS_MAILBOX_INTERFACE+" "+interface)

    if(mbox_busy_Socket1()):
        print "mbox_is_busy not recover after 50 retry"
        sys.exit(1)
    os.system("wrmsr ""-p 25 "+const.MSR_OS_MAILBOX_DATA+" "+str(data))
    os.system("wrmsr ""-p 25 "+const.MSR_OS_MAILBOX_INTERFACE+" "+interface)



def mbox_read_data_interface():

    print "S0:OSmailbox data",commands.getoutput("rdmsr ""-p 1 "+const.MSR_OS_MAILBOX_DATA)
    print "S0:OSMailbox interface",commands.getoutput("rdmsr ""-p 1 "+const.MSR_OS_MAILBOX_INTERFACE)


    print "S1:OSmailbox data",commands.getoutput("rdmsr ""-p 25 "+const.MSR_OS_MAILBOX_DATA)
    print "S1:OSMailbox interface",commands.getoutput("rdmsr ""-p 25 "+const.MSR_OS_MAILBOX_INTERFACE)

    return

def mbox_read(interface):
    mbox_write_data_interface(interface,0x80000000)
    mbox_read_data_interface()

def mbox_write(interface,data):
    mbox_write_data_interface(interface,data)
    mbox_read_data_interface()

const.MSR_OS_MAILBOX_INTERFACE="0xB0"
const.MSR_OS_MAILBOX_DATA="0xB1"
const.MBOX_INTERFACE_RUN_BUSY=0x80000000
