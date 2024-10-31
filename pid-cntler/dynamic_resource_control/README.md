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

This project provides a way to increase computing-resource utilization
on node-level workload and reource optimization by dynamic resource
control with finer-grained resource isolation/allocation technologies
such as Intel RDT, Turboboost, etc.

This project can adjust resource according to workload resource affinity
model and resource affnity to increase host utilization without SLA
violation, and provide suggestions to workload scheduling based on
workload type and host resource usage, including cores, Last-Level-Cache,
Memory Bandwidth, etc.

## Concepts

| Term           | Meaning |
| :------------- | :------ |
| controller     | A deamon running on host, can do actions according to workload SLA, control strategy, workload model and system resource status. |
| control_knobs  | Package that conatins Host-level control knobs can be used for performance tuning for workloads, now includes CAT for Last-Level-Cache allocation and MBA for memory bandwidth allocation, will add more options in the future |
| monitor        | Package that contains workload performance monitor, system status monitor, anomaly detector, etc. |
| strategy       | Package that contains strategies can be used for control, strategy selection & configuration can be set by user. |
| service        | Package that contains APIs for controller|
| monitor_server | A service that can monitor workload SLI(Service Indicator), SLO(Service-Level-Objectives) used by monitor need to be set by user.  |
| workload_server| A service that simulates scheduler, can listen to user for workload add/delete, launch/stop workloads according resource status on different hosts and workload types. |


# Background & Motivation
This project is designed for mix-deployment of Production Workloads(PRs)
and Best Efforts(BEs) on same host.In traditional scheduler, BEs will
suffer from migration if there is any impact on PRs' performance. Now we
can apply more finer-grained control knobs(CAT, MBA, etc.) to do better
resource isolation/allocation to prevent migration under some cases, we
can also send suggestions based on workload affinity model for workload
scheduling to minimize resource contention between different workloads.

## Further Reading

- [Architecture][arch]

[arch]: docs/architecture.md
