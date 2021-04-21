#include "lru.h"

// initial the hashMap and LinkedList
int initLHash()
{
    memset(table, 0, sizeof(table));
    head = (HNode *)malloc(sizeof(HNode));
    tail = (HNode *)malloc(sizeof(HNode));
    if (head == NULL)
    {
        if (tail != NULL)
            free(tail);
        return -1;
    }
    if (tail == NULL)
    {
        free(head);
        return -1;
    }
    head -> lnext = tail;
    tail -> lpre = head;
    return 0;
}

HNode * createHNode(uint32_t srcIP, uint32_t dstIp, uint16_t srcPort, uint16_t dstPort)
{
    HNode * p = NULL;
    p = (HNode *)malloc(sizeof(HNode));
    if (p == NULL)return NULL;
    p -> srcIp = srcIP, p -> dstIP = dstIp, p -> srcPort = srcPort, p -> dstPort = dstPort;
    return p;
}

// compute the hash code 
uint16_t hash(HNode * node)
{
    if (node == NULL)return 0;
    uint16_t res = node->srcIp >> 15 ^ node -> srcIp;
    res ^= (node->dstIP >> 15) ^ node->dstIP;
    res ^= node->srcPort;
    res ^= node->dstPort;
    return res;
}

// compare two node whether equal
int compareNode(HNode * n1, HNode *n2)
{
    if (n1 -> srcIp != n2->srcIp)
        return 0;
    if (n1 -> dstIP != n2->dstIP)
        return 0;
    if (n1->srcPort != n2->srcPort)
        return 0;
    if (n1->dstPort != n2->dstPort)
        return 0;
    return 1;
    
}

int copyHNode(HNode *from, HNode *to)
{
    if (from == NULL || to == NULL)return 0;
    to -> srcIp = from -> srcIp;
    to -> dstIP = from -> dstIP;
    to -> srcPort = from -> srcPort;
    to -> dstPort = from -> dstPort;
    return 1;
}

// insert into hash table
static int insertHash(HNode * node)
{
    uint16_t value = hash(node);
    if (table[value] == NULL)
    {
        table[value] = node;
        node -> pre = NULL;
        node -> next = NULL;
    }
    else
    {
        HNode *p;
        HNode *pre;
        p = table[value];
        for (;p != NULL; p = p -> next)
        {
            if (compareNode(p, node))
            {
                if (fractList(p))
                    insertList(p);
                free(node);
                return 0;
            }
            pre = p;
        }
        pre -> next = node;
        node -> pre = pre;
        node -> next = NULL;
    }
    return 1;
}

// insert into LinkedList
static int insertList(HNode * node)
{
    HNode *pre = tail -> lpre;
    node -> lpre = pre;
    node -> lnext = tail;
    pre -> lnext = node;
    tail -> lpre = node;
    node -> timestamp = clock();
    return 1;
}

static int fractList(HNode *p)
{
    HNode *lp;
    HNode *ln;
    lp = p->lpre;
    ln = p->lnext;
    lp -> lnext = ln;
    ln -> lpre = lp;
    return 1;
}
// insert into LinkedHashMap
void insertLinkedHashMap(HNode * node)
{
    HNode *p;
    p = (HNode *)malloc(sizeof(HNode));
    if (p == NULL)return ;
    if (!copyHNode(node, p))
    {
        free(p);
        return;
    }
    if (insertHash(p))
    {
        insertList(p);
    }
    else
    {
        free(p);
    }
}

static int updateListNode(HNode *node)
{
    if (fractList(node))
        insertList(node);
    return 1;
}

static int removeHashNode(HNode * node)
{
    HNode * pre = node -> pre;
    HNode * next = node -> next;
    if (pre == NULL)
    {
        uint16_t val = hash(node);
        table[val] = next;
    }
    else
    {
        pre -> next = next;
    }
    if (next != NULL)
    {
        next -> pre = pre;
    }
    return 1;
}

static int removeLinkedNode(HNode * node)
{
    if (node == head || node == tail)return 0;
    HNode * pre = node -> lpre;
    HNode * next = node -> lnext;
    pre -> lnext = next;
    next -> lpre = pre;
    return 1;
}

// remove the expired HNode, 当前时间，超时阈值
void expireHNode(uint64_t curT, uint64_t thres)
{
    HNode *p = head -> lnext;
    HNode *pre = head;
    HNode *next = NULL;
    for (; p != tail && p != NULL; p = next)
    {
        next = p -> lnext;
        if (curT - p->timestamp > thres)
        {
            if (removeHashNode(p) && removeLinkedNode(p))
            {
                free(p);
            }
        }else break;
    }
}

int containsKey(HNode * node)
{
    HNode *lhead = table[hash(node)];
    for (; lhead != NULL; lhead = lhead -> next)
    {
        if (compareNode(lhead, node))
        {
            updateListNode(lhead);
            return 1;
        }
    }
    return 0;
}

int containsKeyAndRemove(HNode *node)
{
    HNode *lhead = table[hash(node)];
    for (; lhead != NULL; lhead = lhead -> next)
    {
        if (compareNode(lhead, node))
        {
            if (removeHashNode(lhead) && removeLinkedNode(lhead))
                free(lhead);
            return 1;
        }
    }
    return 0;
}

void destoryList()
{
    while(head)
    {
        HNode * p = head;
        head = head -> lnext;
        free(p);
    }
}

void printAllNodes()
{
    int count = 0;
    HNode * p = head -> lnext;
    while(p != tail)
    {
        printf("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\t当前srcIP为:\t%d", p -> srcIp);
        count ++;
        p = p->lnext;
    }

    printf("\n\t当前节点总数为:\t%d\n", count);
}
