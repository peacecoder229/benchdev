#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <string.h>

#include "lib/pci.h"


#define INTERVAL	1000000  /* sampling rate in microsecond, this is an example: 1s */

#define IMC0_CHANNEL0	0x2042
#define IMC0_CHANNEL1	0x2046
#define IMC0_CHANNEL2	0x204A
#define IMC1_CHANNEL0	0x2042
#define IMC1_CHANNEL1	0x2046
#define IMC1_CHANNEL2	0x204A

#define SOCK_NUM	2
#define CHANNEL_NUM	6  /* skx has 6 channel per socket */
#define EVENT_NUM	4  /* CAS_COUNT, RPQ_INSERTS, RPQ_OCCUPANCY, RPQ_OCCUPANCY:t=0x18 */
#define METRICS		3

#define CAS_COUNT_IND		0
#define RPQ_INSERTS_IND		1
#define RPQ_OCCUPANCY_IND	2
#define RPQ_OCCUPANCY_T_IND	3

#define METRIC_MEM_BW		0
#define METRIC_AVG_LAT		1
#define METRIC_OCCUPANCY	2

double ddr_freq_ghz;
struct pci_dev *imc_dev[SOCK_NUM][CHANNEL_NUM];
unsigned long long counters[SOCK_NUM][EVENT_NUM][CHANNEL_NUM];
double metrics[SOCK_NUM][METRICS];


float get_ddr_freq(void)
{
	float freq = 0;
	char buf[256];
	FILE *fp = NULL;
	char *cmd = "dmidecode  | grep 'Configured Clock Speed:' | grep -v Unknown | head -n 1 | awk '{ print $4 }'";

	fp = popen(cmd, "r");
	if (fp == NULL)
		return -1;
	if (fgets(buf, sizeof(buf) - 1, fp) != NULL)
		sscanf(buf, "%f", &freq);

	pclose(fp);

	/* GHZ */
	return freq / 1000;
}

void write_each_imc(int reg, u32 val)
{
	int sock, chan;
	struct pci_dev *dev;

	for (sock = 0; sock < SOCK_NUM; sock++) {
		for (chan = 0; chan < CHANNEL_NUM; chan++) {
			dev = imc_dev[sock][chan];
			if (dev)
				pci_write_long(dev, reg, val);
		}
	}
}

void set_event(u32 index, u32 val)
{
	u32 base = 0xD8;
	u32 reg = base + index * 4;

	write_each_imc(reg, val);
}

u64 read_counter(struct pci_dev *dev, u32 index)
{
	u32 base = 0xA0;
	u32 reg = base + index * 8;
	u64 val_l, val_h;

	val_l = pci_read_long(dev, reg);
	val_h = pci_read_long(dev, reg + 4);

	return (val_h << 32) + val_l;
}

void get_counters(void)
{
	int sock, chan, evt_ind;
	struct pci_dev *dev;

	memset((void *)counters, 0, sizeof(counters));

	for (sock = 0; sock < SOCK_NUM; sock++) {
		for (evt_ind = 0; evt_ind < EVENT_NUM; evt_ind++) {
			for (chan = 0; chan < CHANNEL_NUM; chan++) {
				dev = imc_dev[sock][chan];
				if (dev)
					counters[sock][evt_ind][chan] = read_counter(dev, evt_ind);
				else
					counters[sock][evt_ind][chan] = 0;
			}
		}
	}
}

void init(void)
{
	/* 1. set box_ctl.frz */
	write_each_imc(0xF4, 0x00000100);

	/* 2. enable couting for each monitor */
	write_each_imc(0xD8, 0x00400000);
	write_each_imc(0xDC, 0x00400000);
	write_each_imc(0xE0, 0x00400000);
	write_each_imc(0xE4, 0x00400000);
        /* write_each_imc(0xE8, 0x00400000); */

	/* 3. select event & umask */
	set_event(CAS_COUNT_IND, 0x00440F04);  /* CAS_COUNT */
	set_event(RPQ_INSERTS_IND, 0x00440010);  /* RPQ_INSERTS */
	set_event(RPQ_OCCUPANCY_IND, 0x00440080);  /* RPQ_OCCUPANCY */
	/* set_event(RPQ_OCCUPANCY_T_IND, 0x18440080); */ /* RPQ_OCCUPANCY with threshhold=0x18 */
	set_event(RPQ_OCCUPANCY_T_IND, 0x14440080);  /* RPQ_OCCUPANCY with threshhold=0x14 */

	/* 4. start counting by unfreezing the counters */
	write_each_imc(0xF4, 0x00000000);
}

void reset_counting(void)
{
	/* reset counter */
	write_each_imc(0xF4, 0x00000002);

}

void stop_counting(void)
{
	/* stop counting */
	write_each_imc(0xF4, 0x00000100);
}

void mem_bw(u64 delta_time)
{
	int sock, chan;

	for (sock = 0; sock < SOCK_NUM; sock++) {
		u64 count = 0;

		for (chan = 0; chan < CHANNEL_NUM; chan++)
			count += counters[sock][CAS_COUNT_IND][chan];

		/* Memory Utilization = CAS_COUNT * 64
		 * Reference to the fomula in P96 of <<Scalable Memory Family Perf Mon 336274.pdf>>
		 */
		metrics[sock][METRIC_MEM_BW] = ((double)(count) * 64 * 1000000000 / delta_time);
		/* to MB/s */
		metrics[sock][METRIC_MEM_BW] = ((double)(metrics[sock][METRIC_MEM_BW]) / 1024 / 1024);
	}
}

void avg_latency(void)
{
	int sock, chan;

	for (sock = 0; sock < SOCK_NUM; sock++) {
		double rpq_inserts = 0;
		double rpq_occupancy = 0;

		for (chan = 0; chan < CHANNEL_NUM; chan++) {
			rpq_inserts += counters[sock][RPQ_INSERTS_IND][chan];
			rpq_occupancy += counters[sock][RPQ_OCCUPANCY_IND][chan];
		}

		if (rpq_inserts)
			metrics[sock][METRIC_AVG_LAT] = rpq_occupancy / rpq_inserts;
		else
			metrics[sock][METRIC_AVG_LAT] = 0; /* should be 0 ? */
	}

}

void occupancy(u64 delta_time)
{
	int sock, chan;

	for (sock = 0; sock < SOCK_NUM; sock++) {
		double occupancy_t = 0;

		for (chan = 0; chan < CHANNEL_NUM; chan++)
			occupancy_t += counters[sock][RPQ_OCCUPANCY_T_IND][chan];

		/* 
		 * %age time heavy queueing:
		 *    RPQ_OCCUPANCY:t=N * 2 * P1_FREQ_GHZ / (delta_rdtsc * DDR_FREQ_GHZ)
		 * == RPQ_OCCUPANCY:t=N * 2 / (delta_time_in_ns * DDR_FREQ_GHZ)
		 *
		 * Multipling 1000 is to make the value more readable
		 */
		metrics[sock][METRIC_OCCUPANCY] = ((double)(occupancy_t) * 2) * 1000 / (delta_time * ddr_freq_ghz);
	}
}

int main(void)
{
	struct pci_dev *dev;
	struct pci_access *pacc;
	struct timespec ts_start, ts_end;
	u64 delta_time;  /* nanosecond */

	pacc = pci_alloc();		/* Get the pci_access structure */
	/* Set all options you want -- here we stick with the defaults */
	pci_init(pacc);		/* Initialize the PCI library */
	pci_scan_bus(pacc);		/* We want to get the list of devices */
	int i, j, k;

	ddr_freq_ghz = get_ddr_freq();
	if (ddr_freq_ghz < 0) {
		//printf("Failed to get DDR freq\n");
		return -1;
	}
	//printf("ddr freq: %f\n", ddr_freq_ghz);

	i = j = 0;
	for (i = 0; i < SOCK_NUM; i++) {
		for (j = 0; j < CHANNEL_NUM; j++)
			imc_dev[i][j] = NULL;
	}

	i = j = k = 0;
	for (dev=pacc->devices; dev; dev=dev->next)	/* Iterate over all devices */
	{

		pci_fill_info(dev, PCI_FILL_IDENT | PCI_FILL_BASES | PCI_FILL_CLASS);	/* Fill in header info we need */

		if (dev->device_id == IMC0_CHANNEL0 || dev->device_id == IMC0_CHANNEL1 || dev->device_id == IMC0_CHANNEL2) {
			if (imc_dev[0][0] == NULL) {
				imc_dev[0][0] = dev;
				j++;
				continue;
			}

			if (imc_dev[0][0]) {
				if (dev->bus == imc_dev[0][0]->bus)
					imc_dev[0][j++] = dev;
				else
					imc_dev[1][k++] = dev;
			}
		}
	}
/*
	for (i = 0; i < SOCK_NUM; i++) {
		printf("---------------------- socket #%d -----------------------\n", i);
		for (j = 0; j < CHANNEL_NUM; j++) {
			struct pci_dev *dev = imc_dev[i][j];
			if (dev)
				printf("%04x:%02x:%02x.%d\n", dev->domain, dev->bus, dev->dev, dev->func);
		}
	}
*/
	init();
/*
	for (i = 0; i < SOCK_NUM; i++) {
		printf("S#%d mem bw(MB/s), S#%d avg latency, S#%d occupancy", i, i, i);
		if (!i)
			printf(",  ");
		else
			printf("\n");
	}
*/
//	for ( ; ; ) {
		reset_counting();

	        clock_gettime(CLOCK_REALTIME, &ts_start);
		usleep(INTERVAL);
	        clock_gettime(CLOCK_REALTIME, &ts_end);
		delta_time = (ts_end.tv_sec - ts_start.tv_sec) * 1000000000 + (ts_end.tv_nsec - ts_start.tv_nsec);

		get_counters();

		memset((void *)metrics, 0, sizeof(metrics));
		mem_bw(delta_time);
		avg_latency();
		occupancy(delta_time);

		/*
		 * printf("delta time: %lu\n", delta_time);
		 */

		for (i = 0; i < SOCK_NUM; i++) {
			printf("%lf, %lf,  %lf", (double)(metrics[i][METRIC_MEM_BW]), (double)metrics[i][METRIC_AVG_LAT], (double)metrics[i][METRIC_OCCUPANCY]);
			if (!i)
				printf(",  ");
			else
				printf("\n");
		}
//	}

	stop_counting();
	pci_cleanup(pacc);		/* Close everything */
	return 0;
}
