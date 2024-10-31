ICPC=/opt/intel/bin/icpc
all: clean test_spinlock atomic_op mutex_lock spin_lock_test progress
test_spinlock:
	gcc  -g -O2 1.c spinlock.s -o test_spinlock -lpthread
atomic_op:
	g++  -g -O2 2.c -o atomic_op -lpthread -std=c++11
mutex_lock:
	gcc  -g -O2 3.c -o mutex_lock -lpthread	
spin_lock_test:
	gcc  -g  spin_lock_test.c spinlock.s -o spin_lock_test -lpthread -D_GNU_SOURCE
progress:
	gcc  -g  4.c spinlock.s -o progress -lpthread

clean:
	rm -f test_spinlock atomic_op mutex_lock spin_lock_test progress
