Note on kerenl module building
obj-m = testmsr.o
It creates testmsr.o object file from testmsr.c and then links them together into testmsr.ko kernel object module

below line provide path to compiled source tree against which the testmsr.o is built!!
make -C /lib/modules/$(shell uname -r)/build M=$PWD modules
this cna be replaced with
make -C /home/vinay/linux-3.9 M=$PWD modules

