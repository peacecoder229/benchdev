#!/bin/bash

BASE_URL="http://cce-docker-cargo.sh.intel.com/docker_images/"

yum install -y docker.io intel-cmt-cat msr-tools memcached redis 

chmod +x tool/hwpdesire.sh

systemctl start docker

unset http_proxy

function download_img()
{
    url=${BASE_URL}/${1}.img.xz
    echo Begin to import $1 image

    curl $url | xzcat - | docker load
}

<<<<<<< HEAD
#download_img stream_omp
download_img rn50
# download_img clucene
#download_img speccpu2006
download_img speccpu2017
#download_img widedeep
#download_img specjbb2005
=======
download_img stream_omp
download_img specjbb2005
# download_img rn50
# download_img clucene
# download_img speccpu2006
# download_img speccpu2017
# download_img widedeep
>>>>>>> 3837d2d4e92a80e432f8f4c953d758d781f09112

echo "Done!"
