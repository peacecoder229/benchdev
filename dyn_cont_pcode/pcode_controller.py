#!/usr/bin/python
# -*- coding: utf-8 -*-


class PcodeController():
    def __init__(self, knob_dic):
        self.knob_dic = knob_dic  # dic

    def decrease_level(self, knob_list):
        for i in knob_list[::-1]:
            if i in self.knob_dic and self.knob_dic[i].decrease_level():
                return True
        return False

    def increase_level(self, knob_list):
        for i in knob_list:
            if i in self.knob_dic and self.knob_dic[i].increase_level():
                return True
        return False

    def increase_levels(self, knob_list, levels):
        for i in range(levels):
            if not self.increase_level(knob_list):
                return i
        return levels

    def decrease_levels(self, knob_list, levels):
        for i in range(levels):
            if not self.decrease_level(knob_list):
                return i
        return levels

    def get_config(self):
        dic = {}
        for k in self.knob_dic.keys():
            dic[k] = self.knob_dic[k].to_dic()
        return dic

if __name__ == "__main__":
    import control_knobs
    PR_COS = '4'
    BE_COS = '5'
    PR_cores = '0-13,28-41'
    BE_cores = '14-27,42-55'
    test_knob_dic = {'hp_hwp':control_knobs.hwp.HWP(0, PR_COS, PR_cores),
                     'lp_cat':control_knobs.cat.CAT(0, BE_COS, BE_cores),
                     'lp_mba':control_knobs.mba.MBA(0, BE_COS, BE_cores)}

    test_pcontroller = PcodeController(test_knob_dic)
    print test_pcontroller.get_config()
    print test_pcontroller.increase_levels(['lp_cat'],4)
    print test_pcontroller.get_config()
