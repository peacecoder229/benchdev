# About WoMix (Workload Mix-deployment) test framework
## What is WoMix?
Womix is a automiation test framework for:
- Workload characterization: Run workloads under pre-definded system configurations, compare performance and/or resoure cousumption.
- Workloads mix-deployment (colocation) benchmarks: Parallel run 2 or more workload instances on same system, observe interference of workloads through performance results or EMON reports.

## How many workloads are supported by WoMix? 
Presently, WoMix supports 
- All int and fp benchmark components of SPECcpu2006 and SPECcpu2017.
- Java based benchmark from SPECjbb2005.
- AI benchmark RN50 (mxnet) and Wide-and-deep benchmark.
- LLC and memory bandwidth noisy generator: stream.
- web based benchmark tools: wrk, openssl and ycsb
- Media encode/decode: ffmpeg
- Search enginer simulator: clucene.

# About automation test process
## How to install WoMix under Centos 7?

- Download EMON from http://goto/emon, install EMON to /opt/intel/sep
- Install framework: `bash ./install.sh`

## How to enable EMON under WoMix?

* Add `source ./hook/emon.inc.sh` after framework imported. When you would do EMON monitoring during workload running.
* By default, this framework will use CLX event list and metrics expression. When you need to capture data from others, please set varable `EMON_CONF="<EMON CONFIG PATH>"` in your script, it contains 2 required files.
    * events.txt: event list (plain text) file
    * metrics.xml: metric expression (xml formatted) file


## How to add new workload list?

1. Edit workload.inc.sh throught text editor, add a new bash function into this file. As recommand, function name should same as the workload name. There are 3 parameters for that function: [str: CPU-set] [str: PATH] [int: THREAD_number]. 
2. Fill your start up command of workload into this function.
    - CPU-set (internal name: $1 ): use container, cgroup, numactl or taskset to limit you workload runs on static CPUs.
    - PATH (internal name: $2 ): a path what will store all files output.
    - THREAD_number (internal name: $3 ): thread number setting if required.
3. Call this workload name in your test scripts with `WORKLOAD=<YOUR FUNCTION NAME>`

## How to run a scaling test for workload inside list?
1. Install workloads will be tested and this test framework on your machines.
2. Follow the previous contents, make scripts for your scaling test. Few tips:
    - Reference the file "scaling_test_example.sh", create your test script. 
      - Change parameters
          - CPUSET=[YOUR_CPUSET] 
          - INSTANCES=[THREAD_number]
          - CAT_RANGE=$(seq [MIN] [MAX]) 
          - MBA_RANGE=$(seq [MIN] [STEP] [MAX]) 
          - FREQ_RANGE=$(seq [MIN] [MAX]) # times 100MHz
          - ROOT_PATH=`date +WW%W.%w-%H%M` # The root path for whole test project, keep default is recommended.
          - WORKLOAD=[YOUR FUNCTION NMAE] # workload function would be called
      - Set scaling knobs. Currently there are 2 knobs can be used. 
          - rdt_sweeping: CAT and MBA sweeping test.
          - frequency_sweeping: sweeping test for CPU frequency.
      - Add advance bash logic codes for test if needed. 
3. Please do not runing any other operations when scaling workloads processing.
4. When scaling test finished, result file were stored by $ROOT_PATH. Please back up that folder is commended.


## How to run HWDRC performance validations
1. Prepare ICX servers with HWDRC patch, enable NUMA. Install WoMiX framework.
2. Install required python packages by: 
   ```
   curl https://gitlab.devtools.intel.com/dea-cce-se/ExperimentalDataReader/-/archive/master/ExperimentalDataReader-master.tar.bz2 | tar xfj - 
   cd ExperimentalDataReader-master
   python3 setup.py install # requires internet connection
   ```
3. goto <WoMiX>/reporter, run `python3 hwdrc_validatio_cases.py -d $( lscpu | grep node1 | awk '{print $4}') -r 60 -s on`, generate test scripts.
4. goto <WoMix>, run all validation scripts by `ls *_colocation.sh | xargs -n 1 sh`
5. go back to <WoMiX>/reporter, run `python3 hwdrc_pass_criterion.py  ../HWDRCValidation/<WWdate>` to capture results for all cases finished.
