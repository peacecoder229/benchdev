import os
from workload import Workload


class Speccpu2006(Workload):
    def __init__(self, PID, cores, COS, resource_list):
        name = 'speccpu2006'
        super(Speccpu2006, self).__init__(name, PID, cores, COS, resource_list)

    def start_workload(self):
        docker_name=str(self.name)+str(self.PID)
        cmd = "docker run --name %s --rm -v `pwd`/SPECcpu/result -e INSTANCES=1 -e WORKLOAD=mcf --cpuset-cpus=%s speccpu2006 >/dev/null &" % (docker_name, self.cores)
        os.system(cmd)

    def stop_workload(self):
        docker_name = str(self.name) + str(self.PID)
        cmd = "docker ps -a | grep %s | awk '{print $1}' | xargs docker rm -f" % docker_name
        os.system(cmd)


if __name__ == "__main__":
    D = Workload('Specjbb2015', '0-55')
