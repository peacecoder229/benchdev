// Copyright 2015 Intel Corporation.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <getopt.h>
#include <signal.h>
#include <sched.h>
#include <sys/types.h>
#include <sys/wait.h>


// Definitions
#define IA32_PERFEVTSEL0         0x186
#define IA32_PERFEVTSEL1         0x187
#define IA32_PERFCTR0            0xc1
#define IA32_PERFCTR1            0xc2
#define IA32_PERFEVT_BRANCH      0x05300c4
#define IA32_PERFEVT_BRANCH_MISS 0x05300c5

#define SLEEP_INTERVAL           250
#define PRINT_LOOP_COUNT         (1000000 / SLEEP_INTERVAL)


// Structures

// Info for a logical core
struct coreinfo {
	uint64_t num;                // Core number
	uint64_t max_freq;           // Maximum available frequency
	uint64_t min_freq;           // Minimum available frequency
	uint64_t cur_freq;           // Current frequency
	uint64_t branch_last;        // Last reading of total branches
	uint64_t branch_miss_last;   // Last reading of branch misses
	char cpufreq_gov[64];        // Name of original cpufreq governor, before we set as userspace
	FILE *setspeed_fp;           // File pointer for scaling_setspeed;
};


// Global data
static unsigned RUN_LOOP = 1;


// Function prototypes

// Print usage information
static void print_help(char *const progname);

// Parse corelist provided, fork a new process for every core, and read data about core
static int parse_corelist_and_fork(char *corelist, double threshold);

// Scale the core to the highest available frequency
static void scale_core_max(struct coreinfo *ci);

// Scale the core to the lowest available frequency
static void scale_core_min(struct coreinfo *ci);

// Apply monitoring policy for given core
static double apply_policy(struct coreinfo *ci, double threshold);

// Set up core counters, and read initial data
static int set_up_core(struct coreinfo *ci);

// Run the main monitoring/scaling loop
static void run_loop(struct coreinfo *ci, double threshold);

// Stop core counters and free resources
static void shut_down_core(struct coreinfo *ci);

// rdpmc
static uint64_t rdpmc(uint64_t counter) {
	uint32_t eax, edx;
	__asm__ __volatile__ ("rdpmc" : "=a"(eax), "=d"(edx) : "c"(counter) : "memory" );
	return (uint64_t) eax | ((uint64_t) edx << 32);
}

// Signal handler
static void signal_handler(int signum) {
	if (signum == SIGINT) {
		RUN_LOOP = 0;
		return;
	}
	if (signum == SIGSEGV) {
		fprintf(stderr, "Fatal: cpu caught signal %d\n", signum);
		exit(-1);
	}
}


// Main
int main(int argc, char * const * argv) {
	char *corelist = NULL, *ratiostr = NULL, *tmp;
	double ratio;
	int c, num_cores, i;
	while ((c = getopt(argc, argv, "hc:r:")) != -1) {
		switch (c) {
		case 'c':
			corelist = optarg;
			break;
		case 'r':
			ratiostr = optarg;
			break;
		case 'h':
		default:
			print_help (argv[0]);
			return 0;
		}
	}
	if (!corelist || !ratiostr) {
		print_help(argv[0]);
		return 0;
	}
	ratio = strtod(ratiostr, &tmp);
	if (tmp == ratiostr) {
		fprintf(stderr, "Error: Invalid ratio: %s\n", ratiostr);
		return 0;
	}
	if ((num_cores = parse_corelist_and_fork(corelist, ratio)) < 0) {
		fprintf(stderr, "Error: Invalid corelist format: %s\n\n", corelist);
		print_help(argv[0]);
		return -1;
	}
	for (i = 0; i < num_cores; i++) {
		wait(NULL);
	}
	return 0;
}


// Function implementation

// Print usage information and help
static void print_help(char *const progname) {
	fprintf(stderr,
		"Monitors the branch miss/hit ratio of the selected cores. If the ratio falls\n"
		"below a specified threshold for a core, then scale down the core to its\n"
		"minimum frequency. Otherwise, scale it up to its maximum frequency\n\n"
		"Usage: %s -c <cores> -r <ratio>\n"
		"  cores = Cores to monitor, e.g. cores 1 and 3 to 5 inclusive can be specified with 1,3-5\n"
		"  ratio = Threshold ratio in decimal. Should be such that 0.0 <= ratio <= 1.0\n", progname);
}

// Parse corelist provided, fork a new process for every core, and read data about core
static int parse_corelist_and_fork(char *corelist, double threshold) {
	int num_cores = 0, low, high, i;
	struct coreinfo *ci = NULL;
	char *p1, *p2;
	pid_t pid;
	p1 = corelist;
	while (isspace(*p1)) {
		p1++;
	}
	while (1) {
		if (!isdigit(*p1)) {
			break;
		}
		low = strtoul(p1, &p2, 10);
		if (p1 == p2) {
			break;
		}
		if (*p2 == '-') {
			p1 = p2 + 1;
			if (!isdigit(*p1)) {
				break;
			}
			high = strtoul(p1, &p2, 10);
			if (p1 == p2) {
				break;
			}
			if (high <= low) {
				break;
			}
			for (i = num_cores; i < num_cores + high + 1 - low; i++) {
				if ((pid = fork()) < 0) {
					perror("fork()");
					exit(-1);
				}
				if (pid == 0) {
					if (!(ci = calloc(1, sizeof(struct coreinfo)))) {
						perror("calloc()");
						exit(-1);
					}
					ci->num = low + i - num_cores;
					cpu_set_t cpu_set;
					CPU_ZERO(&cpu_set);
					CPU_SET(ci->num, &cpu_set);
					if (sched_setaffinity(pid, sizeof(cpu_set), &cpu_set) < 0) {
						perror("sched_setaffinity()");
						exit(-1);
					}
					signal(SIGINT, signal_handler);
					signal(SIGSEGV, signal_handler);
					if (set_up_core(ci) < 0) {
						exit(-1);
					}
					run_loop(ci, threshold);
					shut_down_core(ci);
					exit(0);
				}
			}
			num_cores += high - low + 1;
		} else {
			if ((pid = fork()) < 0) {
				perror("fork()");
				exit(-1);
			}
			if (pid == 0) {
				if (!(ci = calloc(1, sizeof(struct coreinfo)))) {
					perror("calloc()");
					exit(-1);
				}
				ci->num = low;
				cpu_set_t cpu_set;
				CPU_ZERO(&cpu_set);
				CPU_SET(ci->num, &cpu_set);
				if (sched_setaffinity(pid, sizeof(cpu_set), &cpu_set) < 0) {
					perror("sched_setaffinity()");
					exit(-1);
				}
				signal(SIGINT, signal_handler);
				signal(SIGSEGV, signal_handler);
				if (set_up_core(ci) < 0) {
					exit(-1);
				}
				run_loop(ci, threshold);
				shut_down_core(ci);
				exit(0);
			}
			num_cores++;
		}
		if (*p2 == '\0') {
			return num_cores;
		}
		if (*p2 == ',') {
			p1 = p2 + 1;
			continue;
		}
		// Error
		break;
	}
	return -1;
}

// Set up core counters, and read initial data
static int set_up_core(struct coreinfo *ci) {
	int msr_fd;
	FILE *fp;
	uint64_t setup;
	static char filepath[256], buf[256];
	// Read max frequency
	snprintf(filepath, sizeof(filepath), "/sys/devices/system/cpu/cpu%lu/cpufreq/scaling_max_freq", ci->num);
	if (!(fp = fopen(filepath, "r"))) {
		perror("fopen()");
		return -1;
	}
	fscanf(fp, "%lu", &ci->max_freq);
	fclose(fp);
	// Read min frequency
	snprintf(filepath, sizeof(filepath), "/sys/devices/system/cpu/cpu%lu/cpufreq/scaling_min_freq", ci->num);
	if (!(fp = fopen(filepath, "r"))) {
		perror("fopen()");
		return -1;
	}
	fscanf(fp, "%lu", &ci->min_freq);
	fclose(fp);
	printf("Core: { num: %lu, max_freq: %lu, min_freq: %lu }\n",
		ci->num, ci->max_freq, ci->min_freq);
	// Set up MSRs
	snprintf(filepath, sizeof(filepath), "/dev/cpu/%lu/msr", ci->num);
	if ((msr_fd = open(filepath, O_RDWR | O_SYNC)) < 0) {
		fprintf(stderr, "Error opening MSR file for core %lu. (is msr kernel module loaded?)\n", ci->num);
		return -1;
	}
	setup = IA32_PERFEVT_BRANCH;
	if (pwrite(msr_fd, &setup, sizeof(setup), IA32_PERFEVTSEL0) < 0) {
		fprintf(stderr, "Error: Unable to set counter for core %lu\n", ci->num);
		return -1;
	}
	setup = IA32_PERFEVT_BRANCH_MISS;
	if (pwrite(msr_fd, &setup, sizeof(setup), IA32_PERFEVTSEL1) < 0) {
		fprintf(stderr, "Error: Unable to set counter for core %lu\n", ci->num);
		return -1;
	}
	close(msr_fd);
	// Set cpufreq governor as userspace and store old governor
	snprintf(filepath, sizeof(filepath), "/sys/devices/system/cpu/cpu%lu/cpufreq/scaling_governor", ci->num);
	if (!(fp = fopen(filepath, "rw+"))) {
		fprintf(stderr, "Error: Unable to set governor to userspace\n");
		return -1;
	}
	fgets(buf, sizeof(buf), fp);
	strcpy(ci->cpufreq_gov, buf);
	fseek(fp, 0, SEEK_SET);
	fputs("userspace", fp);
	fclose(fp);
	// Open file pointer for scaling_setspeed
	snprintf(filepath, sizeof(filepath), "/sys/devices/system/cpu/cpu%lu/cpufreq/scaling_setspeed", ci->num);
	if (!(ci->setspeed_fp = fopen(filepath, "rw+"))) {
		fprintf(stderr, "Error: Unable to open scaling_setspeed file\n");
		return -1;
	}
	// Set current frequency as max frequency
	scale_core_max(ci);
	return 0;
}

// Apply monitoring policy for given core
static double apply_policy(struct coreinfo *ci, double threshold) {
	uint64_t branch_last, branch_miss_last, branch, branch_miss, branch_diff, miss_diff;
	double ratio;
	branch_last = ci->branch_last;
	branch_miss_last = ci->branch_miss_last;
	branch = rdpmc(0);
	branch_miss = rdpmc(1);
	ci->branch_last = branch;
	ci->branch_miss_last = branch_miss;
	if (branch <= branch_last) {
		// Likely a counter overflow. Skip this round
		return -1.0;
	}
	if (branch_miss <= branch_miss_last) {
		// Likely a counter overflow. Skip this round
		return -1.0;
	}
	branch_diff = branch - branch_last;
	miss_diff = branch_miss - branch_miss_last;
	if (branch_diff < (SLEEP_INTERVAL * 100)) {
		// Likely no workload running on this core. Skip
		return -1.0;
	}
	ratio = (double) miss_diff * ((double) 100 / (double) branch_diff);
	if (ratio < threshold) {
		scale_core_min(ci);
	} else {
		scale_core_max(ci);
	}
	return ratio;
}

// Run monitoring loop
static void run_loop(struct coreinfo *ci, double threshold) {
	double ratio;
	unsigned print = 0;
	while (RUN_LOOP) {
		usleep(SLEEP_INTERVAL);
		print++;
		ratio = apply_policy(ci, threshold);
		if (print > PRINT_LOOP_COUNT) {
			if (ratio < 0.0) {
				printf("core %lu: -no wrkld- %4.fGHz\n",
					ci->num, (double) ci->cur_freq / 1000000.0);
			} else {
				printf("core %lu: %.4f (%lu branches) %4.fGHz\n",
					ci->num, ratio, ci->branch_last,
					(double) ci->cur_freq / 1000000.0);
			}
			print = 0;
		}
	}
}

// Stop core counters and free resources
static void shut_down_core(struct coreinfo *ci) {
	int msr_fd;
	FILE *fp;
	uint64_t setup;
	static char filepath[256];
	// Disable counters
	snprintf(filepath, sizeof(filepath), "/dev/cpu/%lu/msr", ci->num);
	if ((msr_fd = open(filepath, O_RDWR | O_SYNC)) < 0) {
		fprintf(stderr, "Error: Unable to set counter for core %lu\n", ci->num);
		return;
	}
	setup = 0;
	if (pwrite(msr_fd, &setup, sizeof(setup), IA32_PERFEVTSEL0) < 0) {
		fprintf(stderr, "Error: Unable to set counter for core %lu\n", ci->num);
		return;
	}
	setup = 0;
	if (pwrite(msr_fd, &setup, sizeof(setup), IA32_PERFEVTSEL1) < 0) {
		fprintf(stderr, "Error: Unable to set counter for core %lu\n", ci->num);
		return;
	}
	close(msr_fd);
	// Restore cpufreq governor
	snprintf(filepath, sizeof(filepath), "/sys/devices/system/cpu/cpu%lu/cpufreq/scaling_governor", ci->num);
	if (!(fp = fopen(filepath, "w"))) {
		fprintf(stderr, "Error: Unable to set governor to userspace\n");
		return;
	}
	fputs(ci->cpufreq_gov, fp);
	fclose(fp);
	// Close setspeed fp
	fclose(ci->setspeed_fp);
	free(ci);
}

// Scale the core to the highest available frequency
static void scale_core_max(struct coreinfo *ci) {
	fseek(ci->setspeed_fp, 0, SEEK_SET);
	fprintf(ci->setspeed_fp, "%lu", ci->max_freq);
	ci->cur_freq = ci->max_freq;
}

// Scale the core to the lowest available frequency
static void scale_core_min(struct coreinfo *ci) {
	fseek(ci->setspeed_fp, 0, SEEK_SET);
	fprintf(ci->setspeed_fp, "%lu", ci->min_freq);
	ci->cur_freq = ci->min_freq;
}
