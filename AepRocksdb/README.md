Observed huge run to run variations 
After debugging  root cause was shekk was limiting to ulimit -n 1024
Because .bashrc does not set ulimit to -n unlimited.
And db_bench.py script although sets ulmit with os.system CMD , but 
laucnhes db_bench with os.popen(cmd)  in a separate shell which does not 
inherit parent SHEL env!!

So
cmd = "ulimit -n 66566 ; %s" , cmd
