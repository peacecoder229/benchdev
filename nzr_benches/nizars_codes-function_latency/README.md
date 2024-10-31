# Introduction

this main code in this repo is latency.py  this is a bcc code that is meant to use Kprobes inside the kernel to measure the exececutiom time of two different function in kernel.

by tracing two function at a time we can expect delay netween executing two functions.

Please refer to the document "introduciton to tracing " for more informaiton about installation

note that for this tool to work it needs both bcc and bpf installed on your machine.
the installation guide links are in the docx file

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

the latency.py tools is based on funclatency available in the original bcc tools


