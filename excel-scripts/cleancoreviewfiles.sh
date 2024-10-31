#!/bin/bash
sed -i -l 1 's/(EDP ....) name (sample #[0-9]* - #[0-9]*) all events\/metrics are normalized per second unless stated otherwise/metric/' $1
sed -i  -l 1 's/socket . core /core/g' $1
sed -i  -l 1 's/(S.C[0-9]*T[0-9]*)//g' $1
sed -i -l 1 's/cpu /cpu/g' $1

