import os
import time 

HP_COS = "0"
LP_COS = "1"
HP_cores = "0-7,16-23"
LP_cores = "8-15,24-31"
HP_NUM = 8 
LP_NUM = 8 

def clean_env():
    try:
        os.system('rm -rf log/*')
        os.system('rm -rf redis_output/*')
        os.system('pkill -9 redis')
        os.system('pkill -9 memtier')
        cmd = "docker ps -a | grep -E \'stream|specjbb|speccpu\' | awk \'{print $1}\' | xargs docker rm -f"
        os.system(cmd)
    except:
        print "err"


def start_speccpu(cores, instances, workload):
    cmd = "docker run --name speccpu --rm -v `pwd`/speccpu:/SPECcpu/result -e INSTANCES=%s -e WORKLOAD=%s --cpuset-cpus=%s speccpu2006:deadloop &" %(instances, workload, cores)
    os.system(cmd)

def start_redis(cores, port):
    hp_cores = cores
    name = 'redis' + str(time.time())
    os.system('mkdir -p redis_output')
    s_cmd = 'nohup taskset -c %s redis-server --port %s &' % (hp_cores, port)
    c_cmd = 'taskset -c %s memtier_benchmark -s localhost -p %s --pipeline=30 -c 10 -t 10 -d 1000 --key-maximum=42949 --key-pattern=G:G --key-stddev=1177 --ratio=1:1 --distinct-client-seed --randomize --test-time=180 --run-count=1 --hide-histogram &>redis_output/redis%s.log &' % (
    hp_cores, port, port)
    os.system(s_cmd)
    os.system(c_cmd)
    p = os.popen('ps aux |grep *:%s | awk \'{print $5}\' | head -1' % port)
    pid = p.readline()
    return name, pid


def start_stream(cores):
    docker_name = "stream" + str(time.time())
    cmd = "docker run --cpuset-cpus=%s -d --name %s stream:loop 2>&1 &" % (cores, docker_name)
    p = os.popen(cmd)
    pid = p.readline()
    return docker_name, pid


def return_memtier_performance(input_file="redis_output/redis*.log"):
    try:
        output = os.popen('tail -n 1 %s | grep ops' % input_file)
        result = output.read()
        if result == '':
            return -1
        l = result.strip().split('\n')
        fltl = [float(i.split()[-12]) for i in l]
        c = sum(fltl)
        # c = sum(fltl)/len(fltl)
        return c
    except:
        return -1
'''
def run_scaling(control_knob, time_interval=2, sample=5):
    while True:
        name = control_knob.name
        level = control_knob.get_level()
        result = []
        for i in range(sample):
            p = return_memtier_performance()
            result.append(p)
            time.sleep(time_interval)
        print "%s control at level %s:" % (name, level)
        print result 
        if control_knob.increase_level():
            time.sleep(time_interval)
            continue
        else: 
            control_knob.reset_level()
            break
'''        
    
def run_test():
    port_start = 7777
    clean_env()
    start_speccpu(HP_cores, HP_NUM, "bwaves")
    #for i in range(HP_NUM):
    #    start_redis(HP_cores, port_start+i)
    for i in range(LP_NUM):
        start_stream(LP_cores)
    '''
    for i in range(180):
        p = return_memtier_performance()
        if p == -1:
            pass
            #break
        print p
        time.sleep(1)
    '''
    #run_scaling(HP_HWP)
    #run_scaling(LP_CAT)
    #run_scaling(LP_MBA)

run_test()
