# 1.Introductio

This repo contain docker scripts that lauch docker and emon.

Note that for these scripts to run they require multiple prequesitis.

# 2. prerequisits:
   
1. docker && docker images
2. sep driver
3. emon

# 3.  availalble scripts

There are three scripts in that repo

emon_run.sh is a scripts that record emon data for 100 seconds

to use emon_run.sh scripts

    emon_run.sh <Delay> <emon_name> <emon_dir>

    #usage example
    ./emon_run.sh 1 run1 results

emon_run.sh will keep on recording for 100 seconds (can be edited insid the script in the final), in case the scripts is killed the script will catch the ctrl+c respones and stop emon before killing the scripts

the output of the follwing example will Be a creation of the "results" dir in case it didn't exists, then 4 files output files will be created (run1_0.out , run1_v.dat run1_o.dat ). Note that the save location is HARDCODED and you might need to change it based on your running machine

 long_run.sh this scripts will lauch emon and start running mxnet rn50, after it finsihes it will launch another emon and run Tensorflow rn50.

after it finishes it will go to hwpdesire follder that controls frequency using MSR registers and set target freqency, (this need other scripts ). The script will set the freqency at 3.4GHz and repeat the runs, then it will set to 2.7Ghz and repeat the tests. 

the zaza scripts are scripts that controls the voltage of the machine.

they should be copied the same location as hwpdesire folder and might need some changes in hardcded location
after_restart.sh is just a script that lauches docker service and netowkring service.
# 4. Important note

the results of the docker run will be savded in a res/ folder. A lot of these scripts requires hard coding of locbinary names and location.

ideallly the scripts are better used for inspiration rather than actual runs because there might ne some differnces between differnt machine.
