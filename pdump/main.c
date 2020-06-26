#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdlib.h>
#include <getopt.h>
#include <signal.h>
#include <stdbool.h>
#include <net/if.h>
#include <time.h>
#include <rte_cycles.h>
#include <rte_mbuf.h>
#include <rte_eal.h>
#include <rte_common.h>
#include <rte_debug.h>
#include <rte_ethdev.h>
#include <rte_memory.h>
#include <rte_lcore.h>
#include <rte_branch_prediction.h>
#include <rte_errno.h>
#include <rte_dev.h>
#include <rte_kvargs.h>
#include <rte_mempool.h>
#include <rte_ring.h>
#include <rte_string_fns.h>
#include <rte_pdump.h>
#include "rule.h"

#define SRC_PORT 34
#define DST_PORT 36

#define CMD_LINE_OPT_PDUMP "pdump"
#define PDUMP_PORT_ARG "port"
#define PDUMP_PCI_ARG "device_id"
#define PDUMP_QUEUE_ARG "queue"
#define PDUMP_DIR_ARG "dir"
#define PDUMP_HL7_DEV_ARG "hl7-dev"
#define PDUMP_ASTM_DEV_ARG "astm-dev"
#define PDUMP_DICOM_DEV_ARG "dicom-dev"
#define PDUMP_HTTP_DEV_ARG "http-dev"
#define PDUMP_FTP_DEV_ARG "ftp-dev"
#define PDUMP_RING_SIZE_ARG "ring-size"
#define PDUMP_MSIZE_ARG "mbuf-size"
#define PDUMP_NUM_MBUFS_ARG "total-num-mbufs"
#define PDUMP_CAPTURE_TIME_ARG "time"
#define PDUMP_CAPTURE_RESULT_ARG "sql_id"

#define ENABLE_HL7 1
#define ENABLE_DICOM 2
#define ENABLE_HTTP 4
#define ENABLE_FTP 8
#define ENABLE_BOTH 19
#define ENABLE_ASTM 16

#define MP_NAME "pdump_pool_%d"
#define CURRENT_NAME "current_pool_%d"
#define RX_RING "rx_ring_%d_%d"
//#define TX_RING "tx_ring_%d"

#define VDEV_NAME_FMT "net_pcap=%s"
#define VDEV_NAME_FMT_HTTP_FTP "net_pcap=%s%s"
#define VDEV_PCAP_ARGS_FMT "tx_pcap=%s"

#define HL7_STR "hl7"
#define ASTM_STR "astm"
#define DICOM_STR "dicom"
#define HTTP_STR "http"
#define FTP_STR "ftp"

#define TX_STREAM_SIZE 64
#define BURST_SIZE 32


#define MBUF_POOL_CACHE_SIZE 250
#define TX_DESC_PER_QUEUE 512
#define RX_DESC_PER_QUEUE 512
#define MBUFS_PER_POOL 65535
#define RING_SIZE 16384
#define SIZE 256

#define APP_ARG_TCPDUMP_MAX_TUPLES 54

#define POWEROF2(x) ((((x)-1) & (x)) == 0)

union Port {
	char p[2];
	uint16_t port;
} src_port, dst_port;

struct pdump_stats {
	uint64_t dequeue_pkts;
	uint64_t hl7_pkts;
	uint64_t astm_pkts;
	uint64_t dicom_pkts;
	uint64_t http_pkts;
	uint64_t ftp_pkts;
};

struct pdump_tuples {
	/* cli params */
	uint16_t port;
	uint16_t device_id;
	// uint16_t queue;
	char hl7_dev[TX_STREAM_SIZE];
	char dicom_dev[TX_STREAM_SIZE];
	char astm_dev[TX_STREAM_SIZE];
	char http_dev[TX_STREAM_SIZE];
	char ftp_dev[TX_STREAM_SIZE];
	uint32_t ring_size;
	uint16_t mbuf_data_size;
	uint32_t total_num_mbufs;

	/* params for library API call */
	uint8_t dir;
	struct rte_mempool *mp;
	// struct rte_ring *rx_ring;
	//struct rte_ring *tx_ring;

	/* params for packet dumping */
	uint16_t hl7_vdev_id;
	uint16_t dicom_vdev_id;
	uint16_t astm_vdev_id;
	uint16_t http_vdev_id;
	uint16_t ftp_vdev_id;
	// bool single_pdump_dev;
	uint64_t time;
	uint64_t sql_id;

	/* stats */
	struct pdump_stats stats;
} __rte_cache_aligned;

static struct pdump_tuples pdump_t[APP_ARG_TCPDUMP_MAX_TUPLES];
// static struct rte_eth_conf port_conf_default1;
static const struct rte_eth_conf port_conf_default = {
	.rxmode = {
		.max_rx_pkt_len = 70000,
	},
};
static volatile uint8_t quit_signal;
struct rte_mempool *clone_pool;
struct rte_mempool *current_pool;
struct Node * root;
struct Node * root_dicom;
struct Node * root_astm;
struct JudgeFirst * hl7_root;
struct JudgeFirst * dicom_root;
struct JudgeFirst * astm_root;
struct JudgeFirst * http_root;
struct JudgeFirst * ftp_root;
int *dicom_rule;
int dicom_size;
int *http_rule;
int http_size;
int *ftp_rule;
int ftp_size;

struct parse_val {
	uint64_t min;
	uint64_t max;
	uint64_t val;
};

static const char * const valid_pdump_arguments[] = {
	PDUMP_PORT_ARG,
	PDUMP_PCI_ARG,
	PDUMP_DIR_ARG,
	PDUMP_HL7_DEV_ARG,
	PDUMP_ASTM_DEV_ARG,
	PDUMP_DICOM_DEV_ARG,
	PDUMP_HTTP_DEV_ARG,
	PDUMP_FTP_DEV_ARG,
	PDUMP_MSIZE_ARG,
	PDUMP_NUM_MBUFS_ARG,
	PDUMP_CAPTURE_TIME_ARG,
	PDUMP_CAPTURE_RESULT_ARG,
	NULL
};

static int num_tuples;

static void
signal_handler(int sig_num)
{
	if (sig_num == SIGINT) {
		printf("\n\nSignal %d received, preparing to exit...\n",
				sig_num);
		quit_signal = 1;
	}
}

static void
pdump_usage(const char *prgname)
{
	printf("usage: %s [EAL options] -- --pdump "
			"'device_id=<pci id or vdev name>),"
			"port=<port(in TCP UDP) id>",
			"(hl7-dev=<iface or pcap file> |"
			" astm-dev=<iface or pcap file> |"
			" dicom-dev=<iface or pcap file>,"
			"[mbuf-size=<mbuf data size>default:2176],"
			"[total-num-mbufs=<number of mbufs>default:65535]"
			"[time=<number of minutes>default:10]"
			"[sql-id=<number in mysql>default:0]'\n",
			prgname);
}

static int
parse_uint_value(const char *key, const char *value, void *extra_args)
{
	struct parse_val *v;
	unsigned long t;
	char *end;
	int ret = 0;

	errno = 0;
	v = extra_args;
	t = strtoul(value, &end, 10);

	if (errno != 0 || end[0] != 0 || t < v->min || t > v->max) {
		printf("invalid value:\"%s\" for key:\"%s\", "
			"value must be >= %"PRIu64" and <= %"PRIu64"\n",
			value, key, v->min, v->max);
		ret = -EINVAL;
	}
	if (!strcmp(key, PDUMP_RING_SIZE_ARG) && !POWEROF2(t)) {
		printf("invalid value:\"%s\" for key:\"%s\", "
			"value must be power of 2\n", value, key);
		ret = -EINVAL;
	}
	if (ret != 0)
		return ret;

	v->val = t;
	return 0;
}

static int
parse_rxtxdev(const char *key, const char *value, void *extra_args)
{

	struct pdump_tuples *pt = extra_args;

	if (!strcmp(key, PDUMP_HL7_DEV_ARG)) {
		snprintf(pt->hl7_dev, sizeof(pt->hl7_dev), "%s", value);
		/* identify the tx stream type for pcap vdev */
		// if (if_nametoindex(pt->rx_dev))
		// 	pt->rx_vdev_stream_type = IFACE;
	} else if (!strcmp(key, PDUMP_ASTM_DEV_ARG)) {
		snprintf(pt->astm_dev, sizeof(pt->astm_dev), "%s", value);
		/* identify the tx stream type for pcap vdev */
		// if (if_nametoindex(pt->tx_dev))
		// 	pt->tx_vdev_stream_type = IFACE;
	} else if (!strcmp(key, PDUMP_DICOM_DEV_ARG)) {
		snprintf(pt->dicom_dev, sizeof(pt->dicom_dev), "%s", value);
		/* identify the tx stream type for pcap vdev */
		// if (if_nametoindex(pt->tx_dev))
		// 	pt->tx_vdev_stream_type = IFACE;
	} else if (!strcmp(key, PDUMP_HTTP_DEV_ARG)) {
		snprintf(pt->http_dev, sizeof(pt->http_dev), "%s", value);
		/* identify the tx stream type for pcap vdev */
		// if (if_nametoindex(pt->tx_dev))
		// 	pt->tx_vdev_stream_type = IFACE;
	} else if (!strcmp(key, PDUMP_FTP_DEV_ARG)) {
		snprintf(pt->ftp_dev, sizeof(pt->ftp_dev), "%s", value);
		/* identify the tx stream type for pcap vdev */
		// if (if_nametoindex(pt->tx_dev))
		// 	pt->tx_vdev_stream_type = IFACE;
	}

	return 0;
}

static int
parse_pdump(const char *optarg)
{
	struct rte_kvargs *kvlist;
	int ret = 0, cnt1, cnt2, cnt3, cnt4, cnt5;
	struct pdump_tuples *pt;
	struct parse_val v = {0};

	pt = &pdump_t[num_tuples];

	/* initial check for invalid arguments */
	kvlist = rte_kvargs_parse(optarg, valid_pdump_arguments);
	if (kvlist == NULL) {
		printf("--pdump=\"%s\": invalid argument passed\n", optarg);
		return -1;
	}

	/* port/device_id parsing and validation */
	cnt1 = rte_kvargs_count(kvlist, PDUMP_PORT_ARG);
	cnt2 = rte_kvargs_count(kvlist, PDUMP_PCI_ARG);
	if (!(cnt2 == 1)) {
		printf("--pdump=\"%s\": must have "
			"device_id argument\n", optarg);
		ret = -1;
		goto free_kvlist;
	} 
	if (cnt1 == 1) {
		v.min = 1;
		v.max = 65535;
		ret = rte_kvargs_process(kvlist, PDUMP_PORT_ARG,
				&parse_uint_value, &v);
		if (ret < 0)
			goto free_kvlist;
		pt->port = (uint16_t) v.val;
		//pt->dump_by_type = PORT_ID;
	}
	ret = rte_kvargs_process(kvlist, PDUMP_PCI_ARG,
			&parse_uint_value, pt);
	if (ret < 0)
		goto free_kvlist;
	/* rx-dev and tx-dev parsing and validation */
	
	cnt1 = rte_kvargs_count(kvlist, PDUMP_HL7_DEV_ARG);
	cnt2 = rte_kvargs_count(kvlist, PDUMP_DICOM_DEV_ARG);
	cnt3 = rte_kvargs_count(kvlist, PDUMP_HTTP_DEV_ARG);
	cnt4 = rte_kvargs_count(kvlist, PDUMP_FTP_DEV_ARG);
	cnt5 = rte_kvargs_count(kvlist, PDUMP_ASTM_DEV_ARG);
	if (cnt1 == 0 && cnt2 == 0 && cnt3 == 0 && cnt4 == 0 && cnt5 == 0) {
		printf("--pdump=\"%s\": must have either hl7-dev or "
			"dicom-dev or http-dev or ftp-dev or astm-dev argument\n", optarg);
		ret = -1;
		goto free_kvlist;
	}
	pt -> dir = 0;
	if (cnt1 == 1)
	{
		ret = rte_kvargs_process(kvlist, PDUMP_HL7_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		pt -> dir = (pt->dir | ENABLE_HL7);
	}
	if (cnt2 == 1)
	{
		ret = rte_kvargs_process(kvlist, PDUMP_DICOM_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		pt -> dir = (pt->dir | ENABLE_DICOM);
	}
	if (cnt3 == 1)
	{
		ret = rte_kvargs_process(kvlist, PDUMP_HTTP_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		pt -> dir = (pt->dir | ENABLE_HTTP);
	}
	if (cnt4 == 1)
	{
		ret = rte_kvargs_process(kvlist, PDUMP_FTP_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		pt -> dir = (pt->dir | ENABLE_FTP);
	}
	if (cnt5 == 1)
	{
		ret = rte_kvargs_process(kvlist, PDUMP_ASTM_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		pt -> dir = (pt->dir | ENABLE_ASTM);
	}
	/*else if (cnt1 == 1 && cnt2 == 1) {
		ret = rte_kvargs_process(kvlist, PDUMP_HL7_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		ret = rte_kvargs_process(kvlist, PDUMP_DICOM_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
		
        pt -> dir = ENABLE_BOTH;
	} else if (cnt1 == 1) {
		ret = rte_kvargs_process(kvlist, PDUMP_HL7_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
        pt -> dir = ENABLE_HL7;
		// pt->dir = RTE_PDUMP_FLAG_RX;
	} else if (cnt2 == 1) {
		ret = rte_kvargs_process(kvlist, PDUMP_DICOM_DEV_ARG,
					&parse_rxtxdev, pt);
		if (ret < 0)
			goto free_kvlist;
        pt -> dir = ENABLE_DICOM;
		// pt->dir = RTE_PDUMP_FLAG_TX;
	}*/

	/* optional */
	/* ring_size parsing and validation */
	/* mbuf_data_size parsing and validation */
	cnt1 = rte_kvargs_count(kvlist, PDUMP_MSIZE_ARG);
	if (cnt1 == 1) {
		v.min = 1;
		v.max = UINT16_MAX;
		ret = rte_kvargs_process(kvlist, PDUMP_MSIZE_ARG,
						&parse_uint_value, &v);
		if (ret < 0)
			goto free_kvlist;
		pt->mbuf_data_size = (uint16_t) v.val;
	} else
		pt->mbuf_data_size = RTE_MBUF_DEFAULT_BUF_SIZE;

	/* total_num_mbufs parsing and validation */
	cnt1 = rte_kvargs_count(kvlist, PDUMP_NUM_MBUFS_ARG);
	if (cnt1 == 1) {
		v.min = 1025;
		v.max = UINT16_MAX;
		ret = rte_kvargs_process(kvlist, PDUMP_NUM_MBUFS_ARG,
						&parse_uint_value, &v);
		if (ret < 0)
			goto free_kvlist;
		pt->total_num_mbufs = (uint16_t) v.val;
	} else
		pt->total_num_mbufs = MBUFS_PER_POOL;
	
	cnt1 = rte_kvargs_count(kvlist, PDUMP_CAPTURE_TIME_ARG);
	if (cnt1 == 1) {
		v.min = 1;
		v.max = UINT64_MAX;
		ret = rte_kvargs_process(kvlist, PDUMP_CAPTURE_TIME_ARG,
						&parse_uint_value, &v);
		if (ret < 0)
			goto free_kvlist;
		pt -> time = (uint64_t) v.val;
	}
	else
		pt -> time = 10;

	cnt1 = rte_kvargs_count(kvlist, PDUMP_CAPTURE_RESULT_ARG);
	if (cnt1 == 1) {
		v.min = 1;
		v.max = UINT64_MAX;
		ret = rte_kvargs_process(kvlist, PDUMP_CAPTURE_RESULT_ARG,
						&parse_uint_value, &v);
		if (ret < 0)
			goto free_kvlist;
		pt -> sql_id = (uint64_t) v.val;
	}

	num_tuples++;

free_kvlist:
	rte_kvargs_free(kvlist);
	return ret;
}

static int
launch_args_parse(int argc, char **argv, char *prgname)
{
	int opt, ret;
	int option_index;
	static struct option long_option[] = {
		{"pdump", 1, 0, 0},
		{NULL, 0, 0, 0}
	};

	if (argc == 1)
		pdump_usage(prgname);

	/* Parse command line */
	while ((opt = getopt_long(argc, argv, " ",
			long_option, &option_index)) != EOF) {
		switch (opt) {
		case 0:
			if (!strncmp(long_option[option_index].name,
					CMD_LINE_OPT_PDUMP,
					sizeof(CMD_LINE_OPT_PDUMP))) {
				ret = parse_pdump(optarg);
				if (ret) {
					pdump_usage(prgname);
					return -1;
				}
			}
			break;
		default:
			pdump_usage(prgname);
			return -1;
		}
	}
	//int i;
	//for (i = 0; i < argc + 3; i ++)
	    //printf("prase:%s\n", *(argv+i));

	return 0;
}

static inline void
pdump_rxtx(struct rte_mbuf *rxtx_bufs[], const uint16_t nb_in_deq, struct pdump_tuples *p, struct pdump_stats *stats)
{
	/* write input packets of port to vdev for pdump */
    struct rte_mbuf *bufs_hl7[BURST_SIZE];
	struct rte_mbuf *bufs_dicom[BURST_SIZE];
	struct rte_mbuf *bufs_http[BURST_SIZE];
	struct rte_mbuf *bufs_ftp[BURST_SIZE];
	struct rte_mbuf *bufs_astm[BURST_SIZE];

    uint16_t clone_size_hl7 = 0;
	uint16_t clone_size_dicom = 0;
	uint16_t clone_size_http = 0;
	uint16_t clone_size_ftp = 0;
	uint16_t clone_size_astm = 0;

	// /* first dequeue packets from ring of primary process */
	// const uint16_t nb_in_deq = rte_ring_dequeue_burst(ring,
	// 		(void *)rxtx_bufs, BURST_SIZE, NULL);
	//printf(" %d\n", nb_in_deq); 
	
	stats->dequeue_pkts += nb_in_deq;

	if (nb_in_deq) {
		/* then sent on vdev */
        //此处为筛选逻辑
        char *current_data;
        //printf(" %d\n", nb_in_deq);
        for(int i = 0; i < nb_in_deq; i ++)
        {
			if (rte_pktmbuf_data_len(rxtx_bufs[i])<=DST_PORT + 1)
			{
                rte_pktmbuf_free(rxtx_bufs[i]);
				continue;
			}
			if (p->port != 0)
            {
				current_data = rte_pktmbuf_mtod(rxtx_bufs[i], char *);
            	src_port.p[0] = *(current_data + SRC_PORT + 1);
            	src_port.p[1] = *(current_data + SRC_PORT);
            	dst_port.p[0] = *(current_data + DST_PORT + 1);
            	dst_port.p[1] = *(current_data + DST_PORT);
			}
            if (p->port == 0 || p->port == src_port.port || p->port == dst_port.port)
            {
				if(p->dir & ENABLE_HTTP)
				{
					// printf("%d\t%d\n", rte_pktmbuf_pkt_len(rxtx_bufs[i]),rte_pktmbuf_data_len(rxtx_bufs[i]));
					if (ProcessAll(http_root, rxtx_bufs[i]) > 0)
					{
						//printf(" Here \n");
						struct rte_mbuf *s;
						struct rte_mbuf *last;
						s = rxtx_bufs[i];
						bufs_http[clone_size_http] = rte_pktmbuf_clone(s, clone_pool);
						last = bufs_http[clone_size_http];
						s = s -> next;
						while(s != NULL)
						{
							// printf("Here \n");
							s = rte_pktmbuf_clone(s, clone_pool);
							last -> next = s;
							last = s;
							s = s -> next;
						}
						clone_size_http ++;
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
					else if (process_http(http_rule, http_size, rxtx_bufs[i]) > 0)
					{
						if (AddInList(http_root, rxtx_bufs[i]) > 0)
						{
							struct rte_mbuf *s;
							struct rte_mbuf *last;
							s = rxtx_bufs[i];
							bufs_http[clone_size_http] = rte_pktmbuf_clone(s, clone_pool);
							last = bufs_http[clone_size_http];
							s = s -> next;
							while(s != NULL)
							{
								//printf("Here \n");
								s = rte_pktmbuf_clone(s, clone_pool);
								last -> next = s;
								last = s;
								s = s -> next;
							}
							clone_size_http ++;
						}
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
				}
				if(p->dir & ENABLE_FTP)
				{
					//printf("Here \n");
					if (ProcessAllFtp(ftp_root, rxtx_bufs[i]) > 0)
					{
						struct rte_mbuf *s;
						struct rte_mbuf *last;
						s = rxtx_bufs[i];
						bufs_ftp[clone_size_ftp] = rte_pktmbuf_clone(s, clone_pool);
						last = bufs_ftp[clone_size_ftp];
						s = s -> next;
						while(s != NULL)
						{
							//printf("Here \n");
							s = rte_pktmbuf_clone(s, clone_pool);
							last -> next = s;
							last = s;
							s = s -> next;
						}
						clone_size_ftp ++;
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
					else if (process_ftp(ftp_rule, ftp_size, rxtx_bufs[i]) > 0)
					{
						//printf("Here .\n");
						if (AddInListFtp(ftp_root, rxtx_bufs[i])==1)
						//printf("success!\n");
                                                    ;
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
				}
                if (p->dir & ENABLE_HL7)
                {
                    if (ProcessAll(hl7_root, rxtx_bufs[i]) > 0)
					{
						struct rte_mbuf *s;
						struct rte_mbuf *last;
						s = rxtx_bufs[i];
						bufs_hl7[clone_size_hl7] = rte_pktmbuf_clone(s, clone_pool);
						last = bufs_hl7[clone_size_hl7];
						s = s -> next;
						while(s != NULL)
						{
							// printf("Here \n");
							s = rte_pktmbuf_clone(s, clone_pool);
							last -> next = s;
							last = s;
							s = s -> next;
						}
						clone_size_hl7 ++;
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
		            }
                }
                if (p->dir & ENABLE_ASTM)
                {
                    if (ProcessAll(astm_root, rxtx_bufs[i]) > 0)
					{
						struct rte_mbuf *s;
						struct rte_mbuf *last;
						s = rxtx_bufs[i];
						bufs_astm[clone_size_astm] = rte_pktmbuf_clone(s, clone_pool);
						last = bufs_astm[clone_size_astm];
						s = s -> next;
						while(s != NULL)
						{
							// printf("Here \n");
							s = rte_pktmbuf_clone(s, clone_pool);
							last -> next = s;
							last = s;
							s = s -> next;
						}
						clone_size_astm ++;
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
                }
                if(p->dir & ENABLE_DICOM)
                {
                    if (ProcessAll(dicom_root, rxtx_bufs[i]) > 0)
					{
						struct rte_mbuf *s;
						struct rte_mbuf *last;
						s = rxtx_bufs[i];
						bufs_dicom[clone_size_dicom] = rte_pktmbuf_clone(s, clone_pool);
						last = bufs_dicom[clone_size_dicom];
						s = s -> next;
						while(s != NULL)
						{
							// printf("Here \n");
							s = rte_pktmbuf_clone(s, clone_pool);
							last -> next = s;
							last = s;
							s = s -> next;
						}
						clone_size_dicom ++;
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
                }
                if (p->dir & ENABLE_HL7)
				{
					if (process(root, rxtx_bufs[i]) > 0)
					{
						if (AddInList(hl7_root, rxtx_bufs[i]) > 0)
						{
							struct rte_mbuf *s;
							struct rte_mbuf *last;
							s = rxtx_bufs[i];
							bufs_hl7[clone_size_hl7] = rte_pktmbuf_clone(s, clone_pool);
							last = bufs_hl7[clone_size_hl7];
							s = s -> next;
							while(s != NULL)
							{
								// printf("Here \n");
								s = rte_pktmbuf_clone(s, clone_pool);
								last -> next = s;
								last = s;
								s = s -> next;
							}
							clone_size_hl7 ++;
						}
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
				}
				if (p->dir & ENABLE_ASTM)
				{
					if (process(root_astm, rxtx_bufs[i]) > 0)
					{
						if (AddInList(astm_root, rxtx_bufs[i]) > 0)
						{
							struct rte_mbuf *s;
							struct rte_mbuf *last;
							s = rxtx_bufs[i];
							bufs_astm[clone_size_astm] = rte_pktmbuf_clone(s, clone_pool);
							last = bufs_astm[clone_size_astm];
							s = s -> next;
							while(s != NULL)
							{
								// printf("Here \n");
								s = rte_pktmbuf_clone(s, clone_pool);
								last -> next = s;
								last = s;
								s = s -> next;
							}
							clone_size_astm ++;
						}
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
						
					}
				}
				
				if(p->dir & ENABLE_DICOM)
				{
					if (process_dicom(root_dicom, dicom_rule, dicom_size, rxtx_bufs[i]) > 0)
					{
						// printf("start.\n");
						if (AddInList(dicom_root, rxtx_bufs[i]) > 0)
						{
							
							// printf("end.\n");
							struct rte_mbuf *s;
							struct rte_mbuf *last;
							s = rxtx_bufs[i];
							bufs_dicom[clone_size_dicom] = rte_pktmbuf_clone(s, clone_pool);
							last = bufs_dicom[clone_size_dicom];
							s = s -> next;
							while(s != NULL)
							{
								// printf("Here \n");
								s = rte_pktmbuf_clone(s, clone_pool);
								last -> next = s;
								last = s;
								s = s -> next;
							}
							clone_size_dicom ++;
						}
                        rte_pktmbuf_free(rxtx_bufs[i]);
						continue;
					}
				}
			}
            rte_pktmbuf_free(rxtx_bufs[i]);
		}
		if (p->dir & ENABLE_HL7)
		{
        	uint16_t burst_hl7_size = rte_eth_tx_burst(p->hl7_vdev_id, 0,
				bufs_hl7, clone_size_hl7);
        	stats->hl7_pkts += burst_hl7_size;
			if (unlikely(burst_hl7_size < clone_size_hl7)) {
				uint16_t buf;
				for (buf = burst_hl7_size; buf < clone_size_hl7; buf++){
					rte_pktmbuf_free(bufs_hl7[buf]);
				}
			}
		}
		if (p->dir & ENABLE_ASTM)
		{
        	uint16_t burst_astm_size = rte_eth_tx_burst(p->astm_vdev_id, 0,
				bufs_astm, clone_size_astm);
        	stats->astm_pkts += burst_astm_size;
			if (unlikely(burst_astm_size < clone_size_astm)) {
				uint16_t buf;
				for (buf = burst_astm_size; buf < clone_size_astm; buf++){
					rte_pktmbuf_free(bufs_astm[buf]);
				}
			}
		}
		if (p->dir & ENABLE_DICOM)
		{
        	uint16_t burst_dicom_size = rte_eth_tx_burst(p->dicom_vdev_id, 0,
				bufs_dicom, clone_size_dicom);
        	stats->dicom_pkts += burst_dicom_size;
        	if (unlikely(burst_dicom_size < clone_size_dicom)) {
				uint16_t buf;
				for (buf = burst_dicom_size; buf < clone_size_dicom; buf++){
					rte_pktmbuf_free(bufs_dicom[buf]);
				}
			}
		}
		
		if (p->dir & ENABLE_HTTP)
		{
        	uint16_t burst_http_size = rte_eth_tx_burst(p->http_vdev_id, 0,
				bufs_http, clone_size_http);
        	stats->http_pkts += burst_http_size;
        	if (unlikely(burst_http_size < clone_size_http)) {
				uint16_t buf;
				for (buf = burst_http_size; buf < clone_size_http; buf++){
					rte_pktmbuf_free(bufs_http[buf]);
				}
			}
		}

		if (p->dir & ENABLE_FTP)
		{
        	uint16_t burst_ftp_size = rte_eth_tx_burst(p->ftp_vdev_id, 0,
				bufs_ftp, clone_size_ftp);
        	stats->ftp_pkts += burst_ftp_size;
        	if (unlikely(burst_ftp_size < clone_size_ftp)) {
				uint16_t buf;
				for (buf = burst_ftp_size; buf < clone_size_ftp; buf++){
					rte_pktmbuf_free(bufs_ftp[buf]);
				}
			}
		}
	}
}

static void
cleanup_rings(void)
{
	int i;
	struct pdump_tuples *pt;

	for (i = 0; i < num_tuples; i++) {
		pt = &pdump_t[i];

		//if (pt->device_id)
		// free(pt->device_id);

		/* free the rings */
		//if (pt->rx_ring)
		// rte_ring_free(pt->rx_ring);
		//if (pt->tx_ring)
		//rte_ring_free(pt->tx_ring);
	}
}

static void
cleanup_pdump_resources(void)
{
	int i;
	struct pdump_tuples *pt;
	char name[RTE_ETH_NAME_MAX_LEN];

	/* disable pdump and free the pdump_tuple resources */
	for (i = 0; i < num_tuples; i++) {
		pt = &pdump_t[i];

		/* remove callbacks */
		//disable_pdump(pt);

		/*
		* transmit rest of the enqueued packets of the rings on to
		* the vdev, in order to release mbufs to the mepool.
		**/
        // free_ring_data(pt->rx_ring, pt, &pt->stats);
        //free_ring_data(pt->tx_ring, pt, &pt->stats);
		/* Remove the vdev(s) created */
		
		if (pt->dir & ENABLE_HL7)
		{
			rte_eth_dev_get_name_by_port(pt->hl7_vdev_id, name);
			rte_eal_hotplug_remove("vdev", name);
		}

		if (pt->dir & ENABLE_ASTM)
		{
			rte_eth_dev_get_name_by_port(pt->astm_vdev_id, name);
			rte_eal_hotplug_remove("vdev", name);
		}
		
		if (pt->dir & ENABLE_DICOM)
		{
			rte_eth_dev_get_name_by_port(pt->dicom_vdev_id, name);
			rte_eal_hotplug_remove("vdev", name);
		}
		
		if (pt->dir & ENABLE_HTTP)
		{
			rte_eth_dev_get_name_by_port(pt->http_vdev_id, name);
			rte_eal_hotplug_remove("vdev", name);
		}

		if (pt->dir & ENABLE_FTP)
		{
			rte_eth_dev_get_name_by_port(pt->ftp_vdev_id, name);
			rte_eal_hotplug_remove("vdev", name);
		}

	}
	cleanup_rings();
}

static inline int
configure_vdev(uint16_t port_id)
{
	struct ether_addr addr;
	const uint16_t rxRings = 0, txRings = 1;
	int ret;
	uint16_t q;

	if (!rte_eth_dev_is_valid_port(port_id))
		return -1;

	ret = rte_eth_dev_configure(port_id, rxRings, txRings,
					&port_conf_default);
	if (ret != 0)
		rte_exit(EXIT_FAILURE, "dev config failed\n");

	 for (q = 0; q < txRings; q++) {
		ret = rte_eth_tx_queue_setup(port_id, q, TX_DESC_PER_QUEUE,
				rte_eth_dev_socket_id(port_id), NULL);
		if (ret < 0)
			rte_exit(EXIT_FAILURE, "queue setup failed\n");
	}

	ret = rte_eth_dev_start(port_id);
	if (ret < 0)
		rte_exit(EXIT_FAILURE, "dev start failed\n");

	rte_eth_macaddr_get(port_id, &addr);
	printf("Port %u MAC: %02"PRIx8" %02"PRIx8" %02"PRIx8
			" %02"PRIx8" %02"PRIx8" %02"PRIx8"\n",
			port_id,
			addr.addr_bytes[0], addr.addr_bytes[1],
			addr.addr_bytes[2], addr.addr_bytes[3],
			addr.addr_bytes[4], addr.addr_bytes[5]);

	rte_eth_promiscuous_enable(port_id);

	return 0;
}

#define RX_RING_SIZE 1024
#define TX_RING_SIZE 1024

#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250

static inline int
port_init(uint16_t port, struct rte_mempool *mbuf_pool)
{
	struct rte_eth_conf port_conf = port_conf_default;
	const uint16_t rx_rings = 1, tx_rings = 1;
	uint16_t nb_rxd = RX_RING_SIZE;
	uint16_t nb_txd = TX_RING_SIZE;
	int retval;
	uint16_t q;
	struct rte_eth_dev_info dev_info;
	struct rte_eth_txconf txconf;

	if (!rte_eth_dev_is_valid_port(port))
		return -1;

	rte_eth_dev_info_get(port, &dev_info);
	if (dev_info.tx_offload_capa & DEV_TX_OFFLOAD_MBUF_FAST_FREE)
		port_conf.txmode.offloads |=
			DEV_TX_OFFLOAD_MBUF_FAST_FREE;

	/* Configure the Ethernet device. */
	retval = rte_eth_dev_configure(port, rx_rings, tx_rings, &port_conf);
	if (retval != 0)
		return retval;

	retval = rte_eth_dev_adjust_nb_rx_tx_desc(port, &nb_rxd, &nb_txd);
	if (retval != 0)
		return retval;

	/* Allocate and set up 1 RX queue per Ethernet port. */
	for (q = 0; q < rx_rings; q++) {
		retval = rte_eth_rx_queue_setup(port, q, nb_rxd,
				rte_eth_dev_socket_id(port), NULL, mbuf_pool);
		if (retval < 0)
			return retval;
	}

	txconf = dev_info.default_txconf;
	txconf.offloads = port_conf.txmode.offloads;
	/* Allocate and set up 1 TX queue per Ethernet port. */
	for (q = 0; q < tx_rings; q++) {
		retval = rte_eth_tx_queue_setup(port, q, nb_txd,
				rte_eth_dev_socket_id(port), &txconf);
		if (retval < 0)
			return retval;
	}

	/* Start the Ethernet port. */
	retval = rte_eth_dev_start(port);
	if (retval < 0)
		return retval;

	/* Display the port MAC address. */
	struct ether_addr addr;
	rte_eth_macaddr_get(port, &addr);
	printf("Port %u MAC: %02" PRIx8 " %02" PRIx8 " %02" PRIx8
			   " %02" PRIx8 " %02" PRIx8 " %02" PRIx8 "\n",
			port,
			addr.addr_bytes[0], addr.addr_bytes[1],
			addr.addr_bytes[2], addr.addr_bytes[3],
			addr.addr_bytes[4], addr.addr_bytes[5]);

	/* Enable RX in promiscuous mode for the Ethernet device. */
	rte_eth_promiscuous_enable(port);

	return 0;
}

static void
create_mp_ring_vdev(void)
{
	int i;
	uint16_t portid;
	struct pdump_tuples *pt = NULL;
	// struct rte_mempool *mbuf_pool = NULL;
	char vdev_name[SIZE];
	char vdev_args[SIZE];
	char ring_name[SIZE];
	char mempool_name[SIZE];

    snprintf(mempool_name, SIZE, MP_NAME, num_tuples);
    clone_pool = rte_mempool_lookup(mempool_name);
	if(clone_pool ==NULL)
	{
    	clone_pool = rte_pktmbuf_pool_create(mempool_name,
						MBUFS_PER_POOL,
						MBUF_POOL_CACHE_SIZE, 0,
						RTE_MBUF_DEFAULT_BUF_SIZE,
						rte_socket_id());
    	if (clone_pool == NULL) {
			cleanup_rings();
			rte_exit(EXIT_FAILURE,
				"Mempool creation failed: %s\n",
			rte_strerror(rte_errno));
		}
	}
	current_pool = rte_pktmbuf_pool_create("MBUF_POOL", NUM_MBUFS * 2,
		MBUF_CACHE_SIZE, 0, RTE_MBUF_DEFAULT_BUF_SIZE, rte_socket_id());
	if (current_pool == NULL) {
		cleanup_rings();
		rte_exit(EXIT_FAILURE,
			"Mempool creation failed: %s\n",
		rte_strerror(rte_errno));
	}
	for (i = 0; i < num_tuples; i++) {
		pt = &pdump_t[i];
		if (port_init(pt->device_id, current_pool) != 0)
			rte_exit(EXIT_FAILURE, "Cannot init port %"PRIu16 "\n",
					pt->device_id);
		if (pt->dir & ENABLE_HL7) {

			/* create vdevs */
			snprintf(vdev_name, sizeof(vdev_name),
				 VDEV_NAME_FMT, HL7_STR, i);
			snprintf(vdev_args, sizeof(vdev_args),
				 VDEV_PCAP_ARGS_FMT, pt->hl7_dev);
			if (rte_eal_hotplug_add("vdev", vdev_name,
						vdev_args) < 0) {
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"vdev creation failed:%s:%d\n",
					__func__, __LINE__);
			}
			if (rte_eth_dev_get_port_by_name(vdev_name,
							 &portid) != 0) {
				rte_eal_hotplug_remove("vdev", vdev_name);
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"cannot find added vdev %s:%s:%d\n",
					vdev_name, __func__, __LINE__);
			}
			pt->hl7_vdev_id = portid;

			/* configure vdev */
			configure_vdev(pt->hl7_vdev_id);
		} 
		if (pt->dir & ENABLE_ASTM) {

			/* create vdevs */
			snprintf(vdev_name, sizeof(vdev_name),
				 VDEV_NAME_FMT, ASTM_STR, i);
			snprintf(vdev_args, sizeof(vdev_args),
				 VDEV_PCAP_ARGS_FMT, pt->astm_dev);
			if (rte_eal_hotplug_add("vdev", vdev_name,
						vdev_args) < 0) {
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"vdev creation failed:%s:%d\n",
					__func__, __LINE__);
			}
			if (rte_eth_dev_get_port_by_name(vdev_name,
							 &portid) != 0) {
				rte_eal_hotplug_remove("vdev", vdev_name);
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"cannot find added vdev %s:%s:%d\n",
					vdev_name, __func__, __LINE__);
			}
			pt->astm_vdev_id = portid;

			/* configure vdev */
			configure_vdev(pt->astm_vdev_id);
		} 
		if (pt->dir & ENABLE_DICOM) {

			snprintf(vdev_name, sizeof(vdev_name),
				 VDEV_NAME_FMT, DICOM_STR, i);
			snprintf(vdev_args, sizeof(vdev_args),
				 VDEV_PCAP_ARGS_FMT, pt->dicom_dev);
			if (rte_eal_hotplug_add("vdev", vdev_name,
						vdev_args) < 0) {
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"vdev creation failed:"
					"%s:%d\n", __func__, __LINE__);
			}
			if (rte_eth_dev_get_port_by_name(vdev_name,
					&portid) != 0) {
				rte_eal_hotplug_remove("vdev",
						       vdev_name);
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"cannot find added vdev %s:%s:%d\n",
					vdev_name, __func__, __LINE__);
			}
			pt->dicom_vdev_id = portid;

			/* configure vdev */
			configure_vdev(pt->dicom_vdev_id);
		}
		
		if (pt->dir & ENABLE_HTTP) {

			snprintf(vdev_name, sizeof(vdev_name),
				 VDEV_NAME_FMT_HTTP_FTP, HTTP_STR, 
				 pt->dir&ENABLE_BOTH==ENABLE_BOTH?"AHD":pt->dir&ENABLE_HL7?HL7_STR:pt->dir&ENABLE_DICOM?DICOM_STR:pt->dir&ENABLE_ASTM?ASTM_STR:"", i);
			snprintf(vdev_args, sizeof(vdev_args),
				 VDEV_PCAP_ARGS_FMT, pt->http_dev);
			if (rte_eal_hotplug_add("vdev", vdev_name,
						vdev_args) < 0) {
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"vdev creation failed:"
					"%s:%d\n", __func__, __LINE__);
			}
			if (rte_eth_dev_get_port_by_name(vdev_name,
					&portid) != 0) {
				rte_eal_hotplug_remove("vdev",
						       vdev_name);
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"cannot find added vdev %s:%s:%d\n",
					vdev_name, __func__, __LINE__);
			}
			pt->http_vdev_id = portid;

			/* configure vdev */
			configure_vdev(pt->http_vdev_id);
		}
		
		if (pt->dir & ENABLE_FTP) {

			snprintf(vdev_name, sizeof(vdev_name),
				 VDEV_NAME_FMT_HTTP_FTP, FTP_STR,
				 pt->dir&ENABLE_BOTH==ENABLE_BOTH?"AHD":pt->dir&ENABLE_HL7?HL7_STR:pt->dir&ENABLE_DICOM?DICOM_STR:pt->dir&ENABLE_ASTM?ASTM_STR:"", i);
			snprintf(vdev_args, sizeof(vdev_args),
				 VDEV_PCAP_ARGS_FMT, pt->ftp_dev);
			if (rte_eal_hotplug_add("vdev", vdev_name,
						vdev_args) < 0) {
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"vdev creation failed:"
					"%s:%d\n", __func__, __LINE__);
			}
			if (rte_eth_dev_get_port_by_name(vdev_name,
					&portid) != 0) {
				rte_eal_hotplug_remove("vdev",
						       vdev_name);
				cleanup_rings();
				rte_exit(EXIT_FAILURE,
					"cannot find added vdev %s:%s:%d\n",
					vdev_name, __func__, __LINE__);
			}
			pt->ftp_vdev_id = portid;

			/* configure vdev */
			configure_vdev(pt->ftp_vdev_id);
		}
	}
}

static inline void
dump_packets(void)
{
	int i;
	struct pdump_tuples *pt;
	uint64_t start_time = time(NULL);
	uint64_t current_time;
	//printf("NUM_TUPLES : %d \n", num_tuples);

	while (!quit_signal) {
		current_time = (time(NULL) - start_time) / 60;
		for (i = 0; i < num_tuples; i++) {
			//printf("%d\n", i);
			if (current_time >= pt -> time)
				goto save_result;
			pt = &pdump_t[i];
			struct rte_mbuf *bufs[BURST_SIZE];
			const uint16_t nb_rx = rte_eth_rx_burst(pt->device_id, 0,
					bufs, BURST_SIZE);
			if (unlikely(nb_rx == 0))
				continue;
			pdump_rxtx(bufs, nb_rx, pt, &pt->stats);
		}
	}

save_result:
	return;
}

static void
print_pdump_stats(void)
{
	int i;
	struct pdump_tuples *pt;

	for (i = 0; i < num_tuples; i++) {
		printf("##### PDUMP DEBUG STATS #####\n");
		pt = &pdump_t[i];
		printf(" -packets dequeued:			%"PRIu64"\n",
							pt->stats.dequeue_pkts);
		printf(" -packets transmitted hl7 Packets to vdev:		%"PRIu64"\n",
							pt->stats.hl7_pkts);
		printf(" -packets transmitted astm Packets to vdev:		%"PRIu64"\n",
							pt->stats.astm_pkts);
		printf(" -packets transmitted dicom Packets to vdev:			%"PRIu64"\n",
							pt->stats.dicom_pkts);
		printf(" -packets transmitted http Packets to vdev:			%"PRIu64"\n",
							pt->stats.http_pkts);
		printf(" -packets transmitted ftp Packets to vdev:			%"PRIu64"\n",
							pt->stats.ftp_pkts);
	}
}

int main(int argc, char **argv)
{
	int diag;
	int ret;
	int i;
	int tag;

	char c_flag[] = "-c1";
	char n_flag[] = "-n4";
	//char mp_flag[] = " ";
	//"--proc-type=secondary";
	char *argp[argc + 2];
	signal(SIGINT, signal_handler);
	argp[0] = argv[0];
	argp[1] = c_flag;
	argp[2] = n_flag;
	//argp[3] = mp_flag;

	for (i = 1; i < argc; i++)
		argp[i + 2] = argv[i];

	argc += 2;

	diag = rte_eal_init(argc, argp);
	if (diag < 0)
		rte_panic("Cannot init EAL\n");

	if (rte_eth_dev_count_avail() == 0)
		rte_exit(EXIT_FAILURE, "No Ethernet ports - bye\n");


	argc -= diag;
	argv += (diag - 2);

	/* parse app arguments */
	if (argc > 1) {
		ret = launch_args_parse(argc, argv, argp[0]);
		if (ret < 0)
			rte_exit(EXIT_FAILURE, "Invalid argument\n");
	}
	
	
    create_mp_ring_vdev();

    root = init_root();
	root_dicom = init_root();
	root_astm = init_root();
	
    MYSQL * conn = init_sql();
    tag = build_by_sql(root, conn);
	if(tag < 0)
	{
		printf(" Error in conduct hl7 rule tree.\n");
		goto end_software;
	}
	tag = build_by_sql_astm(root_astm, conn);
	if(tag < 0)
	{
		printf(" Error in conduct astm rule tree.\n");
		goto end_software;
	}

	
	dicom_rule = build_to_dicom(&dicom_size, conn);
	tag = build_to_dicom_str(root_dicom, conn);
	if(dicom_rule == NULL || tag < 0)
	{
		printf(" Error in conduct DICOM rule tree.\n");
		goto end_software;
	}


	http_rule = build_to_http(conn, &http_size);
	if(http_rule == NULL)
	{
		printf(" Error in conduct HTTP rule.\n");
		goto end_software;
	}

	ftp_rule = build_to_ftp(conn, &ftp_size);
	if(ftp_rule == NULL)
	{
		printf(" Error in conduct HTTP rule.\n");
		goto end_software;
	}
	
	hl7_root = initList();
	astm_root = initList();
	dicom_root = initList();
	http_root = initList();
	ftp_root = initList();
	
	printf("\n Dictionary Tree conduct successfully.\n");

    // enable_pdump();
    dump_packets();
end_software:
    cleanup_pdump_resources();
    print_pdump_stats();


    ret = rte_eal_cleanup();
    if(ret)
        printf("Error from rte_eal_cleanup(), %d\n", ret);
	FreeList(hl7_root);
	FreeList(astm_root);
	FreeList(dicom_root);
	FreeList(http_root);
	FreeList(ftp_root);
	FreeSpace(root);
	FreeSpace(root_astm);
	FreeSpace(root_dicom);
	free(dicom_rule);
	free(http_rule);
	free(ftp_rule);
	return 0;
}
