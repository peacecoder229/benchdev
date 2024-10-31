# To build the docker


docker build -t nginx-custom .


# To run the nginx with the wrk in the compiled container use the following as an example

docker run --rm --cpuset-cpus=0-24 -e NGINX_CORE=12 -e WRK_THREAD=12 -e CONNECTION=12000 -e DRUATION=120 -e RATE=6000000 nginx-custom:latest


