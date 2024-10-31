#!/usr/bin/python
# -*- coding: utf-8 -*-
import os


class Monitor(object):
    def __init__(self, name="Monitor"):
        self.name = name

    def SLA_function(self, *args):
        pass

    def set_SLA_function(self, function):
        self.SLA_function = function


if __name__ == "__main__":
    D = Monitor("test")
