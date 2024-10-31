this code is bpf codes to trace the entry and exit of kernel latency between two function.

it will display the output to a csv file


the code for two function latency.py


to use it:

python latency.py first_kernel_function -S second_kernel_fuction 


the output wll be displayed in screen and also outputed to csv file : output.csv

to check all kernel functions :

cat /proc/kallsyms

to kill the process:

pkill -9 latency


