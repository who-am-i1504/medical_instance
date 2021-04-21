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

// 源IP、端口在数据包中的开始位置
#define SRC_PORT 34
// 目的IP、端口在数据包中的开始位置
#define DST_PORT 36
// TCP标识位置
#define TCP_TAG 23
// TCP标识的值
#define TCP_TAG_VALUE 6

// 命令行参数
#define CMD_LINE_OPT_PDUMP "pdump"
// 端口参数
#define PDUMP_PORT_ARG "port"
// 网卡参数
#define PDUMP_PCI_ARG "device_id"
// 队列参数
#define PDUMP_QUEUE_ARG "queue"
// 目录
#define PDUMP_DIR_ARG "dir"
// hl7数据采集输出路径
#define PDUMP_HL7_DEV_ARG "hl7-dev"
// astm数据采集输出路径
#define PDUMP_ASTM_DEV_ARG "astm-dev"
// dicom数据采集输出路径
#define PDUMP_DICOM_DEV_ARG "dicom-dev"
// http数据采集输出路径
#define PDUMP_HTTP_DEV_ARG "http-dev"
// ftp数据采集输出路径
#define PDUMP_FTP_DEV_ARG "ftp-dev"
// 环大小
#define PDUMP_RING_SIZE_ARG "ring-size"
// 内存分配大小
#define PDUMP_MSIZE_ARG "mbuf-size"
// 全部内存
#define PDUMP_NUM_MBUFS_ARG "total-num-mbufs"
// 采集时间配置参数
#define PDUMP_CAPTURE_TIME_ARG "time"
// 数据库ID（已弃用）
#define PDUMP_CAPTURE_RESULT_ARG "sql_id"

// 开启HL7数据采集（0x00000001）
#define ENABLE_HL7 1
// 开启DICOM数据采集（0x00000010）
#define ENABLE_DICOM 2
// 开启HTTP数据采集（0x00000100）
#define ENABLE_HTTP 4
// 开启FTP数据采集（0x00001000）
#define ENABLE_FTP 8

// 开启ASTM数据采集（0x00010000）
#define ENABLE_ASTM 16
// 开启三种协议数据采集（0x00010011）
#define ENABLE_BOTH 19

// 关闭HL7数据采集（0x00011110）
#define DISABLE_HL7 30
// 关闭DICOM数据采集（0x00011101）
#define DISABLE_DICOM 29
// 关闭HTTP数据采集（0x00011011）
#define DISABLE_HTTP 27
// 关闭FTP数据采集（0x00010111）
#define DISABLE_FTP 23
// 关闭ASTM数据采集（0x00001111）
#define DISABLE_ASTM 15

#define MP_NAME "pdump_pool_%d"

#define CURRENT_NAME "current_pool_%d"
#define RX_RING "rx_ring_%d_%d"

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

#define RX_RING_SIZE 1024
#define TX_RING_SIZE 1024

#define NUM_MBUFS 8191
#define MBUF_CACHE_SIZE 250

// 端口结构体
union Port {
	char p[2];
	uint16_t port;
} src_port, dst_port;

// 数据包捕获状态
struct pdump_stats {
    // 采集的总数据包数量
	uint64_t dequeue_pkts;
    // 采集的HL7数据包数量
	uint64_t hl7_pkts;
    // 采集的ASTM数据包数量
	uint64_t astm_pkts;
    // 采集的DICOM数据包数量
	uint64_t dicom_pkts;
    // 采集的HTTP数据包数量
	uint64_t http_pkts;
    // 采集的FTP数据包数量
	uint64_t ftp_pkts;
};

// 配置参数
struct pdump_tuples {
    // 采集数据端口号
	uint16_t port;
    // 采集数据网卡设备
	uint16_t device_id;
    // HL7采集数据的输出路径
	char hl7_dev[TX_STREAM_SIZE];
    // DICOM采集数据的输出路径
	char dicom_dev[TX_STREAM_SIZE];
    // ASTM采集数据的输出路径
	char astm_dev[TX_STREAM_SIZE];
    // HTTP采集数据的输出路径
	char http_dev[TX_STREAM_SIZE];
    // FTP采集数据的输出路径
	char ftp_dev[TX_STREAM_SIZE];
    // 环大小
	uint32_t ring_size;
    // 内存大小
	uint16_t mbuf_data_size;
    // 总内存大小
	uint32_t total_num_mbufs;

	/* params for library API call */
	uint8_t dir;
	struct rte_mempool *mp;

    // 生成的HL7虚拟网卡设备id
	uint16_t hl7_vdev_id;
    // 生成的DICOM虚拟网卡设备id
	uint16_t dicom_vdev_id;
    // 生成的ASTM虚拟网卡设备id
	uint16_t astm_vdev_id;
    // 生成的HTTP虚拟网卡设备id
	uint16_t http_vdev_id;
    // 生成的FTP虚拟网卡设备id
	uint16_t ftp_vdev_id;
    // 采集数据的持续时间
	uint64_t time;
    // 数据采集状态
	struct pdump_stats stats;
} __rte_cache_aligned;

static struct pdump_tuples pdump_t[APP_ARG_TCPDUMP_MAX_TUPLES];
// 采集网卡的配置
static const struct rte_eth_conf port_conf_default = {
	.rxmode = {
		.max_rx_pkt_len = ETHER_MAX_LEN,
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

static int num_tuples = 0;

// 信号处理函数
static void signal_handler(int);

// 数据包处理
static inline void pdump_rxtx(struct rte_mbuf *rxtx_bufs[], const uint16_t nb_in_deq, struct pdump_tuples *p, struct pdump_stats *stats);

// 清除已分配的资源
static void cleanup_pdump_resources(void);

// 清除环
static void cleanup_rings(void);

// 配置内存，网卡设备
static inline int configure_vdev(uint16_t port_id);

// 网卡配置初始化
static inline int port_init(uint16_t port, struct rte_mempool *mbuf_pool);

// 创建环、虚拟网卡设备
static void create_mp_ring_vdev(void);

// 数据采集超时判定
static inline void dump_packets(void);

// 打印数据采集数据
static void print_pdump_stats(void);

// 初始化HL7规则字典树
int initHL7(const char *);

int initDICOM(const char *);

int initASTM(const char *);

int initHTTP(const char *);

int initFTP(const char *);

int initPort(int);

int initDevice(int);

int initParams(int MSIZE, int MBUFS, uint64_t capture_time);

void end_software(void);

void start_capture(char *c_flag, char * n_flag);
