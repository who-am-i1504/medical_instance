#ifndef LRUHASH_H_
#define LRUHASH_H_
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

struct Node {
    uint32_t srcIp, dstIP;
    uint16_t srcPort, dstPort;
    int tag;
    uint64_t timestamp;

    struct Node * pre;
    struct Node * next;
    struct Node * lpre;
    struct Node * lnext;
};

#define HNode struct Node
#define HSIZE 65536


HNode *table[HSIZE];
HNode *head, *tail;

// 初始化链表和哈希表
int initLHash();

// 创建节点
HNode * createHNode(uint32_t, uint32_t, uint16_t, uint16_t);

// hash值 计算
uint16_t hash(HNode *);
// 两节点比较
int compareNode(HNode *, HNode *);
int copyHNode(HNode *, HNode *);

// 插入hash表
static int insertHash(HNode *);
// 插入链表
static int insertList(HNode *);
// 断开链表节点
static int fractList(HNode *);
// 插入链表和哈希表
void insertLinkedHashMap(HNode *);

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
int containsKeyAndRemove(HNode *);

// 释放所有空间
void destoryList();
void printAllNodes();
#endif //LRUHASH_H_
