# WoMiX installation for HWDRC validation project
1. Install womix:
```
    #git clone https://gitlab.devtools.intel.com/dea-cce-se/womix.git && cd womix && git checkout HWDRC_ICX_postsi
    #cd .. && git clone https://gitlab.devtools.intel.com/longcui/hwdrc_postsi.git 
    #mv hwdrc_postsi womix/
    #cd womix && sh install.sh 
```

2. Install required python packages for data summary tool:
```
    #curl https://gitlab.devtools.intel.com/dea-cce-se/ExperimentalDataReader/-/archive/master/ExperimentalDataReader-master.tar.bz2
    #tar -vxf ExperimentalDataReader-master.tar.bz2
    #cd ExperimentalDataReader-master
    #python3 setup.py install
```

# workload associated with 4 mclos (Case #7)
* Notice: For current version, WoMiX only supports mix-deployment over 4 instance of single workload, MLC is suggested.*
1. download **[MLC](https://software.intel.com/content/www/us/en/develop/articles/intelr-memory-latency-checker.html)** and decompress it. Copy file "Linux/mlc" tp /usr/bin/mlc.
2. Modify file "quatro_mlc.sh", CORE_1 to CORES_4 as cores sets for each instances.
3. Execute command `sh quatro_mlc.sh` to begin the test, wait test finish, results should like 
```
For Baseline results:
                GROUP1 = 45404.1
                GROUP2 = 45225.9
                GROUP3 = 44175.1
                GROUP4 = 44040.8
For HWDRC results:
                GROUP1 = 44183.5
                GROUP2 = 44892.7
                GROUP3 = 44165.8
                GROUP4 = 45504.3

```

# HP LP workloads mix-deployment benchmark (case #8 and case #9)
1. Run all test cases:
```
#cd report && python3 hwdrc_validatio_cases.py -d $( lscpu | grep node1 | awk '{print $4}') -r 60 -s on
#cd .. && ls *_colocation.sh | xargs -n 1 sh
```

2. Summary all results:
```
#cd report && python3 hwdrc_pass_criterion.py  ../HWDRCValidation/<WWdate>

======Performance validation with HP and LP mix-deployment======


------Case state (5.00% as threshold)------
mlc_benchmark + mlc_benchmark: PASS

        BASE:   HP=104,641.9,                   LP=72,092.5,
        RDT :   HP=163,054.9,                   LP=3,615.0,
        DRC :   HP=155,245.6,                   LP=14,057.5,


bwaves + bwaves: PASS

        BASE:   HP=346.0,                       LP=268.0,
        RDT :   HP=418.0,                       LP=15.2,
        DRC :   HP=418.0,                       LP=156.0,


libquantum + bwaves: PASS

        BASE:   HP=2,080.0,                     LP=476.0,
        RDT :   HP=2,400.0,                     LP=15.3,
        DRC :   HP=2,560.0,                     LP=0.0,


libquantum + mlc_benchmark: PASS

        BASE:   HP=2,420.0,                     LP=120,436.0,
        RDT :   HP=2,440.0,                     LP=2,918.5,
        DRC :   HP=2,510.0,                     LP=28,248.9,
.....

```
