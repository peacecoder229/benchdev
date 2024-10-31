#!/usr/bin/env python3 

import os

HP_WL = ["specjbb","rn50", "widedeep", "mlc_benchmark"]
LP_WL = ["rn50","specjbb","mlc_benchmark", "bwaves"]


class CPUcores(int):

    @staticmethod
    def from_bit(b):
        return CPUcores(b, 2)

    @staticmethod
    def from_hex(h):
        return CPUcores(h, 16)

    @staticmethod
    def from_desc(core_desc):
        cores = 0
        begin, end = -1, -1
        tmp = 0

        def set_mask(b, e):
            src = 0
            if b == -1:
                b = e
            if b > e:
                b, e = e, b
            for i in range(b, e + 1):
                src = src | (1 << i)
            return src

        for s in core_desc:
            c = ord(s)
            if 47 < c and 58 > c:
                tmp = tmp * 10 + c - 48
                continue

            end = tmp
            if begin == -1:
                begin = tmp

            if c != 45:
                cores |= set_mask(begin, end)
                begin = -1

            tmp = 0

        cores |= set_mask(begin, tmp)
        return CPUcores(cores)

    def __str__(self):
        core_id, step = 0, 0
        desc = []

        def fmt(curr_core, step):
            step -= 1
            if step == 0:
                return "%s" % (curr_core)
            if step == 1:
                return "%s,%s" % (curr_core - 1, curr_core)
            return "%s-%s" % (curr_core - step, curr_core)

        while core_id <= self.bit_length():
            if 1 << core_id & self:
                step += 1
            elif step > 0:
                desc.append(fmt(core_id - 1, step))
                step = 0

            core_id += 1

        return ",".join(desc)

    def __iter__(self):
        core_id = 0
        while core_id <= self.bit_length():
            if 1 << core_id & self:
                yield core_id
            core_id += 1

    def __len__(self):
        tmp, length = self, 0
        while tmp > 0:
            length += 1
            tmp &= (tmp - 1)

        return length

    def all_cores(self):
        return ",".join(map(str, self))


def get_hp_lp_cores(all_cores, ratio):
    core_set = CPUcores.from_desc(all_cores)
    total_cores = len(core_set)
    hp_cores = []   
    lp_cores = []   
    i = 0
    for core in core_set:
        i+=1
        if i <= (total_cores * ratio / 100):
            hp_cores.append(str(core))
        else:
            lp_cores.append(str(core))

    hp_cores = CPUcores.from_desc(",".join(hp_cores))
    lp_cores = CPUcores.from_desc(",".join(lp_cores))

    return (hp_cores, lp_cores)


def creat_script(hp, lp, conf):
    filename = "../%s-%s_colocation.sh"%(hp, lp)

    with open(filename, "w") as fd:
        for row in conf:
            fd.write(row)
            fd.write("\n")
    
    os.chmod(filename, 755)


if __name__ == "__main__":
    import optparse

    parser = optparse.OptionParser()
    parser.add_option("-d", "--desc", dest="desc", action="store",
                      type="string", help="input core set description")
    
    parser.add_option("-r", "--ratio", dest="ratio", action="store",
                      type="int", help="input hp core ratio")    

    parser.add_option("-s", "--ht", dest="ht", action="store",
                      type="string", help="HT on/off")

    (options, args) = parser.parse_args()

    if options.ht.lower() == "off":
        hp_0, lp_0 = get_hp_lp_cores(options.desc, options.ratio)

    else:
        ht0, ht1 = get_hp_lp_cores(options.desc, 50)
        hp_0, lp_0 = get_hp_lp_cores(ht0.all_cores(), options.ratio)
        hp_1, lp_1 = get_hp_lp_cores(ht1.all_cores(), options.ratio)

        hp_0 = CPUcores.from_desc("%s,%s"%(hp_0, hp_1))
        lp_0 = CPUcores.from_desc("%s,%s"%(lp_0, lp_1))
        
    for hp in HP_WL:
        for lp in LP_WL:
            conf = [
                "#!/bin/bash", "", 
                "source process/hwdrc_process.inc.sh", 
                "source hook/pqos_msr.inc.sh", 
                "# source hook/emon.inc.sh", "",
                "LP_CAT=0xfff",
                "LP_MBA=10 # change it if needed", "",
                ]

            conf.append("HP_CORES=%s" % str(hp_0))
            conf.append("LP_CORES=%s" % str(lp_0))

            conf.append("HP_INSTANCES=%s" % len(hp_0))
            conf.append("LP_INSTANCES=%s" % len(lp_0))

            conf.append("hp=%s" % hp)
            conf.append("lp=%s" % lp)
            conf.append( "mba_scaling $hp $lp")
            conf.append("#KEEP_LP_RUNNING=0")
            conf.append( "workload_pair $hp $lp")

            creat_script(hp, lp, conf)
