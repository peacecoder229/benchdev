# readctr_ko
This is a extreme light-weight performance monitoring tool based on RDPMC. It can be used for micro-second level CPU performance metrics collection.
- Kernel module to enable CR4 and program the RDPMC controllers.
- Client works in user space to collect raw data from controllers.

# How to build up
- Dependencies:  kernel-dev, kernel-headers is required.
- Compile process:
    * Execute 'make module' to compile the kernel module.
    * Execute 'make client' to compile the user space tool.
    * Execute 'make' to compile them both and try to enable test enviroments directly.

# How to use
Inside this folder, root permission is required.
- Exec 'insmod readctr.ko' to attach kernel module.
- Exec 'echo1 > /sys/devices/cpu/rdpmc' to enable rdpmc configurations in system level. 
- Exec './mon_client <interval> <iteration>' to capture system telemetries. 2 parameters enabled for this tool:
    - <interval> set sampling intervals by micro-second, 100 as default.
    - <iteration> set the capture iterations, -1 as default, -1 means "forever" (ctrl_c to stop capturing).
- Exec 'rmmod readctr' to disable kernel module.