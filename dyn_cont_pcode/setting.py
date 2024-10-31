#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import control_knobs
import workloads


class Setting(object):
    def __init__(self, PR_COS='4', BE_COS='5', PR_cores='0-7', BE_cores='8-16', platform='skx'):
        self.PR = {}
        self.BE = {}
        self.BE_COS = BE_COS
        self.PR_COS = PR_COS
        self.BE_cores = BE_cores
        self.PR_cores = PR_cores
        self.platform = platform
        '''
        self.control_knobs = [control_knobs.hwp.HWP(0, PR_COS, PR_cores),
                              control_knobs.cat.CAT(0, BE_COS, BE_cores),
                              control_knobs.mba.MBA(0, BE_COS, BE_cores)]
        '''
        self.control_knobs = {'hp_hwp': control_knobs.hwp.HWP(0, PR_COS, PR_cores),
                              'lp_cat': control_knobs.cat.CAT(0, BE_COS, BE_cores),
                              'lp_mba': control_knobs.mba.MBA(0, BE_COS, BE_cores)}
        '''
        self.PR_CAT = control_knobs.cat.CAT(0, PR_COS, PR_cores)
        self.PR_MBA = control_knobs.mba.MBA(0, PR_COS, PR_cores)
        self.BE_CAT = control_knobs.cat.CAT(0, BE_COS, PR_cores)
        self.BE_MBA = control_knobs.mba.MBA(0, BE_COS, PR_cores)
        '''

    def add_BE(self, BE):
        if self.BE.has_key(BE.PID):
            pass
            # TODO
        else:
            self.BE.setdefault(BE.PID, BE)

    def add_PR(self, PR):
        if self.PR.has_key(PR.PID):
            pass
            # TODO
        else:
            self.PR.setdefault(PR.PID, PR)

    def get_PR(self):
        return self.PR

    def get_BE(self):
        return self.BE

    def detach_PR(self, PID):
        if self.PR.has_key(PID):
            workload = self.PR.pop(PID)
            return workload
        else:
            # TODO
            pass

    def detach_BE(self, PID):
        if self.BE.has_key(PID):
            workload = self.BE.pop(PID)
            return workload
        else:
            # TODO
            pass

    def set_PR_cores(self, PR_cores):
        self.PR_cores = PR_cores

    def get_PR_cores(self):
        return self.PR_cores

    def set_BE_cores(self, BE_cores):
        self.BE_cores = BE_cores

    def get_BE_cores(self):
        return self.BE_cores

    def get_control_knobs(self):
        i = 0
        dic = {}
        for ck in self.control_knobs:
            dic.setdefault(i, self.control_knobs[ck].to_dic())
        return dic

    def set_control_knobs(self, cks):
        self.control_knobs = cks

    def reset_resource(self, control_knobs):
        try:
            for i in control_knobs:
                i.reset_level()
            return True
        except:
            print "Cannot reset resource"
            exit(0)


if __name__ == "__main__":
    C = Setting()
