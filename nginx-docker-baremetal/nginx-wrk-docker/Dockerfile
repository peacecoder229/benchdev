FROM centos:7
#FROM ubuntu

ENV http_proxy "http://proxy-us.intel.com:911"
ENV https_proxy "http://proxy-us.intel.com:912"

#RUN /usr/bin/apt install nginx
#RUN apt update && apt install nginx python3
RUN yum install -y nginx python3

ENV NGINX_CORE 16
ENV WORK_THREAD 64
ENV CONNECTION 16000
ENV DRUATION 120
ENV RATE 680000
ENV CONTENT_FILE "4kb.bin"

COPY appstatdata.py /root/appstatdata.py
COPY nginx_custom.conf  /root/nginx_custom.conf
COPY start.sh  /root/start.sh
COPY wrk /root/wrk

COPY 1kb.bin /usr/share/nginx/html/1kb.bin
COPY 1mb.bin /usr/share/nginx/html/1mb.bin
COPY 4kb.bin /usr/share/nginx/html/4kb.bin


CMD ["sh", "-c", "/root/start.sh"]

