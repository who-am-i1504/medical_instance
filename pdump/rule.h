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
int process(struct Node *, struct rte_mbuf *);
int process_dicom(struct Node *, int *, int, struct rte_mbuf *);
int process_http(int *, int, struct rte_mbuf *);
int process_ftp(int *, int, struct rte_mbuf *);

#endif //UNTITLED_RULE_H
