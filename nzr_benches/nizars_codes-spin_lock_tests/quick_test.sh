echo "testing with one thead"
./test_spinlock 1
echo "testing with numa "
numactl -C 0-27,56-83 -m 0 ./test_spinlock
echo "testing regular"
./test_spinlock 
