pkill -9 cpu_stres
echo "sleeping "
sleep 1
./cpu_stress 56 &
perf stat -e cpu_clk_unhalted.ref_tsc,cpu_clk_unhalted.thread,cycles -I 1000 ./cpu_stress 56 &
perf stat -a -e tsc -I 1000
