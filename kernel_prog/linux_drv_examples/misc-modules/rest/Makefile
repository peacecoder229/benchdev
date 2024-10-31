#kernel make file
ifneq ($(KERNELRELEASE),)
	obj-m := hellop.o 

# Otherwise we were called directly from the command
# # line; invoke the kernel build system.
else
#
	KERNELDIR ?= /lib/modules/$(shell uname -r)/build
	PWD  := $(shell pwd)
#
default:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules
endif
