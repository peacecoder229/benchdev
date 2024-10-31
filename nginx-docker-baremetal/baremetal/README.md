# Running baremetal nginx and wrk as one script

./nginx-test.sh 0-23 680000 24000 24-47 8080 24 1kb.bin

First Argument: Nginx Cores

Second Argument: Rate

Third Argument: Number of Connections

Fourth Argument: Worker Cores

Fifth Argument: Port Number

Sixth Argument: Number of threads

Seventh Argument: Filename

# Download wrk and make

https://github.com/wg/wrk

# Download wrk2 and make

https://github.com/giltene/wrk2

The difference between wrk and wrk2 is that wrk2 allows to have a parameter rate at which traffic is generated. 

# Setup

cp -r html-nginx-contents/* /usr/share/nginx/

The line below, launches nginx with two cores and uses port 80

./start-nginx 0-1 80

You can launch wrk or wrk2 as follows:

numactl --membind=1 --physcpubind=32-35 ./wrk/wrk -t 4 -c 400 -d 300s -L http://127.0.0.1:9090/1K


Once basic test is done. You can run automated scripts. Depending on which machine you are using. The scripts provided were tested on icx with 32 cores and spr with 48 cores. Create a new copy if you are testing a different platform.
