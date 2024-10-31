current_dir=${pwd}
echo $current_dir
hwp_dir="/mnt/original_pnp/pnpdata_original/hwpdesire"
cd $current_dir

./emon_run.sh 1 mx_rn50 turbo_2 &

docker run -e BATCH_SIZE=128 -e OMP_NUM_THREADS=26 mx_rn50:latest &> res/run3/turbo_mxnet.txt


./emon_run.sh 1 tf_rn50 turbo_2 &

time docker run -e BATCH_SIZE=128 -e OMP_NUM_THREADS=26 tf_rn50_nizar:latest > res/run3/turbo_tf.txt

cd $hwp_dir
./zaza_34

cd $current_dir

./emon_run.sh 1 mx_rn50 freq_34_2 &

 docker run -e BATCH_SIZE=128 -e OMP_NUM_THREADS=26 mx_rn50:latest &> res/run3/34_mxnet.txt

 ./emon_run.sh 1 tf_rn50 freq_34_2 &

 time docker run -e BATCH_SIZE=128 -e OMP_NUM_THREADS=26 tf_rn50_nizar:latest > res/run3/34_tf.txt

 cd $hwp_dir

 ./zaza_27
 
cd $current_dir

 ./emon_run.sh 1 mx_rn50 freq_27_2 &

 docker run -e BATCH_SIZE=128 -e OMP_NUM_THREADS=26 mx_rn50:latest &> res/run3/27_mxnet.txt

./emon_run.sh 1 tf_rn50 freq_27_2 &

time docker run -e BATCH_SIZE=128 -e OMP_NUM_THREADS=26 tf_rn50_nizar:latest > res/run3/27_tf.tx

