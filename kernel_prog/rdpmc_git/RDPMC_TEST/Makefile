#obj-m = testmsr.o
obj-m = rdmsrbmk.o
KVERSION = $(shell uname -r)
all:
	make -C /lib/modules/$(KVERSION)/build M=$(PWD) modules
clean:
	make -C /lib/modules/$(KVERSION)/build M=$(PWD) clean	
	rm -Rf results.tar.bz2
	rm -Rf results/* 


