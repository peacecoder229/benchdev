obj-m = readctr.o
KVERSION = $(shell uname -r)

all:
	make -C /lib/modules/$(KVERSION)/build M=$(PWD) modules
	${CC} client.c -lpthread -o mon_client
	rmmod readctr.ko
	insmod  readctr.ko

	dmesg -c | less
clean:
	make -C /lib/modules/$(KVERSION)/build M=$(PWD) clean        

client:
	${CC} client.c -lpthread -o mon_client

module:
	make -C /lib/modules/$(KVERSION)/build M=$(PWD) modules
	insmod  readctr.ko
