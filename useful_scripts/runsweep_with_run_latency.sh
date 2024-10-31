#!/bin/bash
./run_lat_rev2.py --basebufsize=2048 --runno=10 --cmd=latency -i 500 --latbwsweep=Yes --maxcore=64  --corestep=64
./run_lat_rev2.py --basebufsize=2048 --runno=16 --cmd=latency -i 500 --latbwsweep=Yes --maxcore=64  --corestep=32
./run_lat_rev2.py --basebufsize=2048 --runno=24 --cmd=latency -i 500 --latbwsweep=Yes --maxcore=64  --corestep=16
./run_lat_rev2.py --basebufsize=2048 --runno=32 --cmd=latency -i 500 --latbwsweep=Yes --maxcore=64  --corestep=8
./run_lat_rev2.py --basebufsize=2048 --runno=32 --cmd=latency -i 500 --latbwsweep=Yes --maxcore=64  --corestep=4



