//
// Created by white on 2019/10/22.
//

#ifndef UNTITLED_RULE_H
#define UNTITLED_RULE_H

#include <stdlib.h>
#include "mysql.h"
#include <rte_mbuf.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <libconfig.h>

//#define MAXCHAR 40
#define MAXCHAR 256

#define SB '\x0b'
#define EB '\x1c'
#define CR '\x0d'

#define HOST "10.246.229.255"
#define USERNAME "remote"
#define PASSWORD "beauty1234."
#define DATABASE "medical"
#define THRE_HOLD 120

#define ETH_IPV4_TAG 12
#define ETH_IPV4_TAG_VALUE 8
#define ETH_IPV4_TAG_VALUE1 524288
#define IP_LENGTH_TAG 14
#define IP_LENGTH_UNIT 4

struct Node {
    struct Node *next[MAXCHAR];
    char ch;
    int danger;
};

union AllIP{
    uint32_t ip[2];
    uint64_t ip_all;
};

union AllPort{
    uint16_t port[2];
    uint32_t port_all;
};

struct FiveGroup{
    union AllIP src_dst;
    union AllPort out_in;
};

struct JudgeFirst {
    struct JudgeFirst *ahead;
    struct FiveGroup src;
    struct FiveGroup dst;
    struct JudgeFirst *next;
};

union Transfer {
	char p[4];
	int number;
} ch_trans_int;

struct JNode {
    struct FiveGroup src;
    struct FiveGroup dst;
	int tag;
    uint64_t timestamp;

    struct JNode * pre;
    struct JNode * next;
    struct JNode * lpre;
    struct JNode * lnext;
};

#define HNode struct JNode
#define HSIZE 65536


HNode *table[HSIZE];
HNode *head, *tail;

uint8_t get_8_num(struct rte_mbuf *target, int place);
uint16_t get_16_num(struct rte_mbuf *target, int place);
uint32_t get_32_num(struct rte_mbuf *target, int place);
uint64_t get_64_Num(struct rte_mbuf *target, int place);

int ETH_IPV4(struct rte_mbuf *target);
int InterIPV4(struct rte_mbuf *target, int);
int InternetIPv4AndLength(struct rte_mbuf * target, int);
int TCPLength(struct rte_mbuf * target, int start);
// 初始化链表和哈希表
int initLHash();

// 创建节点
HNode * createHNode(uint32_t, uint32_t, uint16_t, uint16_t);

// hash值 计算
uint16_t hash(HNode *);
// 两节点比较
int compareNode(HNode *, HNode *);
int copyHNode(HNode *, HNode *);
HNode * copyReverseHNode(HNode *);
// 插入hash表
static int insertHash(HNode *);
// 插入链表
static int insertList(HNode *);
// 断开链表节点
static int fractList(HNode *);
// 插入链表和哈希表
int insertLinkedHashMap(HNode *);

// 更新链表节点时间
static int updateListNode(HNode*);

// 移除哈希节点
static int removeHashNode(HNode *);
// 移除链表节点
static int removeLinkedNode(HNode *);
// 移除超时节点
void expireHNode(uint64_t, uint64_t);

// 判断key是否存在
int containsKey(HNode *);
HNode* getKey(HNode * node);
int containsKeyAndRemove(HNode *);
int removeHNode(HNode * );
// 释放所有空间
void destoryList();
void printAllNodes();

HNode * convertHNode(struct rte_mbuf *, int, int);

struct JudgeFirst * initList();
int Ftp_PORT(struct JudgeFirst *, struct rte_mbuf *);
int Ftp_227(struct JudgeFirst *, struct rte_mbuf *);
int AddInList(struct JudgeFirst *, struct rte_mbuf *);
int AddInListFtp(struct JudgeFirst *, struct rte_mbuf *);
int DeleteFromList(struct JudgeFirst *);
int EqualGroup(struct JudgeFirst *, uint64_t , uint32_t );
int EqualGroupFtp(struct JudgeFirst *, uint32_t , uint16_t ,uint32_t , uint16_t);
int ProcessAll(struct JudgeFirst *, struct rte_mbuf *);
int ProcessAllFtp(struct JudgeFirst *, struct rte_mbuf *);
void FreeList(struct JudgeFirst *);

MYSQL * init_sql();
void show(const char *, const int);
void FreeSpace(struct Node *);
struct Node * init();
struct Node * init_root();
int build(struct Node *, char **, int);
int build_by_sql(struct Node *, MYSQL *);
int build_by_sql_astm(struct Node *, MYSQL *);
int* build_to_http(MYSQL *, int *);
int* build_to_ftp(MYSQL *, int *);
int* build_to_dicom(int *, MYSQL *);
int build_to_dicom_str(struct Node *, MYSQL *);
int add(struct Node *,const char *);
int getIndex(char);
int process(struct Node *, struct rte_mbuf *,int);
int process_dicom(struct Node *, int *, int, struct rte_mbuf *,int);
int process_http(int *, int, struct rte_mbuf *,int);
int process_ftp(int *, int, struct rte_mbuf *,int);

#endif //UNTITLED_RULE_H
