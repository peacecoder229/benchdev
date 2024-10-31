## Introduction

This repo as several binaries and codes that increment a variaible 2^24~= 16 million times within a multithreaded enviroment. this is mean to test differnt type of lock performance.

	# 1.c is using userspace spinlock

	# 2.c using atomic operation for increment (no locks, atomic operatiom perform operation in 1 cycle)

	# 3.c is using mutex locks, mutex lock are managed by the OS and it is perform via system call in kernel the different code test multiple approaches for lucks such as mutex lock, spin lock and atomic approaching to bypass locks all toghether

	# 4.c is similar to 1.c but it also inform you of the progress while running the code (10% , 20% ...) 

	# 5 deadlock.py is  BPF tool that allow us to detect deadlocks

	# spin_locks_test.c is the verison of the code that also pins each thread to a differnt core in a round robin fashion


the goal of this code is to test application behaviour of using mutex (OS managed) and spin_lock which is  user space managed

to run the code you first need to compile the code.

to compile and run you can use. (GCC is needed to compile this code)
	
	make # this will clean previous build and generate new binraies


this will generate the binaries

this will generate 5 binaries ech with name:
	
1.c => test_spinlock
	
2.c => atomic_op

3.c => mutex_lock

spin_lock_test.c => spin_lock_test

4.c => progress 

once biniaries are generated we can use them to generate as many threads as we want

	./mutex_lock 12 # this will generate a code with 12 thrads managed by the scheduler to execute the loops. Once finished it will print out the runtime wuthin usec accuray.

	./mutex_lock # This will generate the default number of threads which 36 threads 
		

	
