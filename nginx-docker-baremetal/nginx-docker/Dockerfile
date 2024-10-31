FROM centos

ENV http_proxy "http://proxy-shz.intel.com:912"
ENV https_proxy "http://proxy-shz.intel.com:912"

RUN dnf install -y nginx python3 lsof net-tools initscripts

#EXPOSE 80

#ENV NGINX_CORE=$1

COPY nginx_custom.conf  /root/nginx_custom.conf
COPY start-nginx.sh  /root/start-nginx.sh

COPY 1kb.bin /usr/share/nginx/html/1kb.bin
COPY 1mb.bin /usr/share/nginx/html/1mb.bin
COPY 4kb.bin /usr/share/nginx/html/4kb.bin
COPY html-nginx-contents/ /usr/share/nginx/html/

#ENTRYPOINT ["tail", "-f", "/dev/null", "/root/start-nginx.sh"]

CMD ["/root/start-nginx.sh"]

