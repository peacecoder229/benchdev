<!--
Copyright (c) 2018 Intel Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

## Overview

This project provides a way to identify workload's affinity to resources
throuth PCA(Principal component analysis) and CF(Collaborative Filtering).
This code is just for reference

## Baseline Workloads(Training Workloads)

Workloads that can get SLI(Service Level Indicator), in this project we
collect emon data of Baseline Workload under different configurations and
then use corrcoef(Pearson Correlation Coefficient) to get the coefficient
between SLI and emon metrics, the coefficient will be used to define the
resource affinity of Baseline Workloads and then these tagged workloads
will be used by CF.

## Test Workloads

Workloads that cannot get SLI, we collect emon data of Test Workloads and
then

## Work Flow

1. Collect Baseline Workloads' emon data and SLI data.
2. Use corrcoef to get its type.(Only LLC and Memory Bandwidth in reference code)
3. Use PCA to get components matrix(vector for 1-component PCA) of Baseline Workloads.
4. Collect Test Workloads' emon data.
5. Use PCA to get components matrix of Test Workloads.
6. Use CF to get the type of Test Workload.(Cos distance is used in reference code.)

## Why PCA and CF

This project use PCA as descending dimension algorithm to get the component
matrix of emon metrics. For Test Workloads, we cannot get SLI which
means that we cannot use supervised method such as LDA, PCA is simple and
widely use as unsupervised descending dimension algorithm, we also tried
DBN in theano but it will bring more overhead for training and inference.
We use CF to do recommendation tool because that now we have not develeped
a universal for workload affinity due to lack of data from different
workloads and configuration. However, we can try more complicated model with
more data collected.

## Data

Data we used comes from SPECjbb2015 and stream running on same host under
different configuration(CAT, MBA, Core Numbers). We collect emon data and
use edp service to get analysis result.
