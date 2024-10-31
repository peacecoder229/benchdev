#msr access
def rdmsr(cpu_num,reg):
    print "rdmsr",cpu_num,reg
    f=open("/dev/cpu/1/msr","r") 
    f.seek(reg)
    print "msr:",f.tell(), f.read(8)
    return 1
