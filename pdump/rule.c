//
// Created by white on 2019/10/22.
//
#include "rule.h"

struct JudgeFirst * initList()
{
    struct JudgeFirst * root;
    root = (struct JudgeFirst *)malloc(sizeof(struct JudgeFirst));
    if (root == NULL)
        return NULL;
    root -> next = root;
    root -> ahead = root -> next;
    root -> src.src_dst.ip_all = 0;
    root -> src.out_in.port_all = 0;
    root -> dst.src_dst.ip_all = 0;
    root -> dst.out_in.port_all = 0;

    return root;
}

int AddInList(struct JudgeFirst * root, struct rte_mbuf * target)
{
    struct JudgeFirst * current;
    struct JudgeFirst * p;
    struct rte_mbuf * mbuf = target;
    int current_length;
    current_length = rte_pktmbuf_data_len(target);
    char *q;
    q = rte_pktmbuf_mtod(target, char *);
    if (current_length < 40)
        return 0;
    char * src = q + 26;
    char * dst = q + 30;
    char * src_port = q + 34;
    char * dst_port = q + 36;
	//printf("\t%x\t%x \t", *((uint32_t *)src), *((uint16_t *)src_port));
    current = (struct JudgeFirst *)malloc(sizeof(struct JudgeFirst));
    if (current == NULL)
        return -1;
    current -> src.src_dst.ip[0] = *(uint32_t *)src;
    current -> src.src_dst.ip[1] = *(uint32_t *)dst;
    current -> src.out_in.port[0] = *(uint16_t *)src_port;
    current -> src.out_in.port[1] = *(uint16_t *)dst_port;
    current -> dst.src_dst.ip[0] = current -> src.src_dst.ip[1];
    current -> dst.src_dst.ip[1] = current -> src.src_dst.ip[0];
    current -> dst.out_in.port[0] = current -> src.out_in.port[1];
    current -> dst.out_in.port[1] = current -> src.out_in.port[0];
    p = root -> ahead;
    p -> next = current;
    root ->ahead = current;
    current -> next = root;
    current -> ahead = p;
	//printf("\t%x\t%x\t%x\t%x \n", current -> src.src_dst.ip_all, current -> dst.src_dst.ip_all, current -> src.out_in.port_all, current -> dst.out_in.port_all);
	/*p = root -> next;
	while(p != root)
	{
		printf(" %x\t%x\t%x\t%x \n", p -> src.src_dst.ip_all, p -> dst.src_dst.ip_all, p -> src.out_in.port_all, p -> dst.out_in.port_all);
		p = p -> next;
	}*/
    return 1;
}

int Ftp_227(struct JudgeFirst * root, struct rte_mbuf * target)
{
	struct JudgeFirst * current;
    struct JudgeFirst * p;
    struct rte_mbuf * mbuf = target;
    int current_length;
    current_length = rte_pktmbuf_data_len(target);
    char *q;
    q = rte_pktmbuf_mtod(target, char *);
    if (current_length < 40)
        return 0;
    char * dst = q + 30;
    char * dst_port = q + 36;
	//printf("\t%x\t%x \t", *((uint32_t *)src), *((uint16_t *)src_port));
    if (current == NULL)
        return -1;
	
	union src_ip_trans{
		char s[4];
		uint32_t src_ip;
	} cur_ip;
	cur_ip.src_ip = 0;
	uint16_t src_port1 = 0;
	uint16_t src_port2 = 0;
	int i = 54;
	for(i = 54; *(q + i) != '(' && i < current_length; i++)
	{
		continue;
	}
	uint8_t status = 0;
	if (i == current_length)
		return 0;
	for (int j = i; *(q + j) != ')' && j < current_length; j++)
	{
		if (status >= 6)
			return 0;
		if (*(q + j) == '(')
			continue;
		if (*(q + j) == ',')
		{
			status += 1;
			continue;
		}
		if (status < 4)
		{
			cur_ip.s[status] *= 10;
			cur_ip.s[status] += *(q + j) - '0';
		}
		else
		{
			if (status == 4)
			{
				src_port1 *= 10;
				src_port1 += *(q + j)  - '0';
			}
			else if (status == 5)
			{
				src_port2 *= 10;
				src_port2 += *(q + j)  - '0';
			}
		}

	}
	union src_port_trans{
		char s[2];
		uint16_t src_ip;
	} cur_port, mid_trans;
	cur_port.src_ip = src_port1*256 + src_port2;
	mid_trans.s[1] = cur_port.s[0];
	mid_trans.s[0] = cur_port.s[1];
    current = (struct JudgeFirst *)malloc(sizeof(struct JudgeFirst));
	current -> src.src_dst.ip[0] = cur_ip.src_ip;
    current -> src.src_dst.ip[1] = *(uint32_t *)dst;
	current -> src.out_in.port[0] = mid_trans.src_ip;
    current -> src.out_in.port[1] = *(uint16_t *)dst_port;
    current -> dst.src_dst.ip[0] = current -> src.src_dst.ip[1];
    current -> dst.src_dst.ip[1] = current -> src.src_dst.ip[0];
    current -> dst.out_in.port[0] = current -> src.out_in.port[1];
    current -> dst.out_in.port[1] = current -> src.out_in.port[0];
    p = root -> ahead;
    p -> next = current;
    root ->ahead = current;
    current -> next = root;
    current -> ahead = p;
    return 1;
}

int Ftp_PORT(struct JudgeFirst * root, struct rte_mbuf * target)
{
	struct JudgeFirst * current;
    struct JudgeFirst * p;
    struct rte_mbuf * mbuf = target;
    int current_length;
    current_length = rte_pktmbuf_data_len(target);
    char *q;
    q = rte_pktmbuf_mtod(target, char *);
    if (current_length < 40)
        return 0;
    char * dst = q + 30;
    char * dst_port = q + 36;
	//printf("\t%x\t%x \t", *((uint32_t *)src), *((uint16_t *)src_port));
    if (current == NULL)
        return -1;
	
	union src_ip_trans{
		char s[4];
		uint32_t src_ip;
	} cur_ip;
	cur_ip.src_ip = 0;
	uint16_t src_port1 = 0;
	uint16_t src_port2 = 0;
	int i = 54;
	for(i = 54; *(q + i) != ' ' && i < current_length; i++)
	{
		continue;
	}
	uint8_t status = 0;
	if (i == current_length)
		return 0;
	for (int j = i + 1; ((*(q + j) <= '9' && *(q + j) >= '0') || *(q + j) == ',') && j < current_length; j++)
	{
		if (status >= 6)
			return 0;
		if (*(q + j) == ' ')
			continue;
		if (*(q + j) == ',')
		{
			status += 1;
			continue;
		}
		if (status < 4)
		{
			cur_ip.s[status] *= 10;
			cur_ip.s[status] += *(q + j) - '0';
		}
		else
		{
			if (status == 4)
			{
				src_port1 *= 10;
				src_port1 += *(q + j)  - '0';
			}
			else if (status == 5)
			{
				src_port2 *= 10;
				src_port2 += *(q + j)  - '0';
			}
		}

	}
	union src_port_trans{
		char s[2];
		uint16_t src_ip;
	} cur_port, mid_trans;
	cur_port.src_ip = src_port1*256 + src_port2;
	mid_trans.s[1] = cur_port.s[0];
	mid_trans.s[0] = cur_port.s[1];
    current = (struct JudgeFirst *)malloc(sizeof(struct JudgeFirst));
	current -> src.src_dst.ip[0] = cur_ip.src_ip;
    current -> src.src_dst.ip[1] = *(uint32_t *)dst;
	current -> src.out_in.port[0] = mid_trans.src_ip;
    current -> src.out_in.port[1] = *(uint16_t *)dst_port;
    current -> dst.src_dst.ip[0] = current -> src.src_dst.ip[1];
    current -> dst.src_dst.ip[1] = current -> src.src_dst.ip[0];
    current -> dst.out_in.port[0] = current -> src.out_in.port[1];
    current -> dst.out_in.port[1] = current -> src.out_in.port[0];
    p = root -> ahead;
    p -> next = current;
    root ->ahead = current;
    current -> next = root;
    current -> ahead = p;
    return 1;
}

int AddInListFtp(struct JudgeFirst * root, struct rte_mbuf * target)
{
	struct JudgeFirst * current;
    struct JudgeFirst * p;
    struct rte_mbuf * mbuf = target;
    int current_length;
    current_length = rte_pktmbuf_data_len(target);
    char *q;
	union transfer_rule {
		char character[4];
		int number;
	} pasv1, pasv2;
	memcpy(pasv1.character, "227 ", sizeof(char) * 4);
	memcpy(pasv2.character, "PORT", sizeof(char) * 4);
	if (current_length > 59)
	{
                //printf("enter judge\n");
        char* data = rte_pktmbuf_mtod(target, char *); 
		memcpy(ch_trans_int.p, data + 54,sizeof(char) * 4);
		if (pasv1.number == ch_trans_int.number)
                {
                     //printf("pasv\n");
			return Ftp_227(root, target);
                }
		if (pasv2.number == ch_trans_int.number)
                {
                     //printf("port\n");
			return Ftp_PORT(root, target);
                }
		
		/*for(int i = 0; i < size; i++)
		{
			if (ch_trans_int.number == *(num + i))
				return 1;
		}*/
	}
    return 0;
	
}

int DeleteFromList(struct JudgeFirst * node)
{
    if (node -> next == node)
        return 0;
    struct JudgeFirst *last;
    last = node -> ahead;
    last -> next = node -> next;
    node -> next -> ahead = last;
    free(node);
    return 1;
}

int EqualGroup(struct JudgeFirst *root, uint64_t ip, uint32_t port)
{
	//printf("%x\t%x\t%x\t%x\n", root -> src.src_dst.ip_all, root -> src.out_in.port_all, ip, port);
    if (root -> src.src_dst.ip_all == ip && root -> src.out_in.port_all == port)
        return 0;
    if (root -> dst.src_dst.ip_all == ip && root -> dst.out_in.port_all == port)
        return 0;
    return -1;
}

int EqualGroupFtp(struct JudgeFirst *root, uint32_t src_ip, uint16_t src_port, uint32_t dst_ip, uint16_t dst_port)
{
    if (root -> src.src_dst.ip[0] == src_ip && root -> src.out_in.port[0] == src_port)
        return 0;
    if (root -> src.src_dst.ip[0] == dst_ip && root -> src.out_in.port[0] == dst_port)
        return 0;
    return -1;
}

int ProcessAll(struct JudgeFirst *root, struct rte_mbuf *target)
{
    struct JudgeFirst *q;
    struct rte_mbuf * mbuf = target;
    int current_length;
    current_length = rte_pktmbuf_data_len(target);
    struct Node * current;
    current = root;
    char *p;
    p = rte_pktmbuf_mtod(target, char *);
    if (current_length < 40)
        return 0;
    uint64_t * ipAddr = p + 26;
    uint32_t * portAddr = p + 34;
    uint16_t * flags = p + 46;
    q = root -> next;
    while(q != root)
    {
//printf(" %ld\t%ld \n", *(ipAddr), *(portAddr));
        if (EqualGroup(q, *(ipAddr), *(portAddr)) == 0)
        {
            if ((*(flags) & 1) && DeleteFromList(q) > 0)
            {
                return 1;
            }
            return 1;
        }
        q = q -> next;
    }
    return 0;
}

int ProcessAllFtp(struct JudgeFirst *root, struct rte_mbuf *target)
{
    struct JudgeFirst *q;
    struct rte_mbuf * mbuf = target;
    int current_length;
    current_length = rte_pktmbuf_data_len(target);
    struct Node * current;
    current = root;
    char *p;
    p = rte_pktmbuf_mtod(target, char *);
    if (current_length < 40)
        return 0;
    uint16_t * flags = p + 46;
    uint32_t * src_ip = p + 26;
    uint32_t * dst_ip = p + 30;
    uint32_t * src_port = p + 34;
    uint32_t * dst_port = p + 36;
    q = root -> next;
	if (*src_port == 20 || *dst_port == 20)
		return 1;
    while(q != root)
    {
//printf(" %ld\t%ld \n", *(ipAddr), *(portAddr));
        if (EqualGroupFtp(q, *(src_ip), *(src_port),*(dst_ip),*(dst_port)) == 0)
        {
            if ((*(flags) & 1) && DeleteFromList(q) > 0)
            {
                return 1;
            }
            return 1;
        }
        q = q -> next;
    }
    return 0;
}

void FreeList(struct JudgeFirst *root)
{
    struct JudgeFirst * p;
    struct JudgeFirst * q;
    p = root -> next;
    for(;p != root;)
    {
        q = p -> next;
        free(p);
        p = q;
    }

    free(root);
}

MYSQL * init_sql()
{
    MYSQL *conn;
    conn = mysql_init(NULL);
	char * host = HOST;
	char *username = USERNAME;
	char *password = PASSWORD;
	char *database = DATABASE;
	int port = 3306;
    if(!conn)
    {
        printf("\n mysql_init failed. \n");
        exit(-1);
    }
	config_t cfg;
	config_init(&cfg);
	if (!config_read_file(&cfg, "pdump.cfg"))
	{
		printf(" No config file about mysql. so use the default config.\n");
		config_destroy(&cfg);
	}
	else
	{
		if (config_lookup_string(&cfg, "HOST", &host))
		{
			printf(" MySql HOST ip is : %s. \n", host);
		}
		if (config_lookup_string(&cfg, "USERNAME", &username))
		{
			printf(" MySql Connect username is : %s. \n", username);
		}
		if (config_lookup_string(&cfg, "PASSWORD", &password))
		{
			printf(" MySql Connect password is : *********. \n");
		}
		if (config_lookup_int(&cfg, "PORT", &port))
		{
			printf(" MySql Connect password is : %d. \n", port);
		}
		
	}
    conn = mysql_real_connect(conn, host,
        username, password, database, port, NULL, 0);
    if(conn)
    {
        printf("\n Connection success.\n");
		config_destroy(&cfg);
        return conn;
    }
    printf("\n Connection failed.\n");
	config_destroy(&cfg);
    exit(1);
}

void show(const char *func, const int line)
{
    printf("\n Error in Function : %s and Line : %d \n", func, line);
}

void FreeSpace(struct Node * root)
{
    for (int i = 0; i < MAXCHAR && root != NULL; i++)
    {
        FreeSpace(root->next[i]);
    }
    if (root != NULL)
        free(root);
}
struct Node * init()
{
    struct Node *root;
    root = (struct Node *)malloc(sizeof(struct Node));
    if (root == NULL)
        return NULL;
    root -> ch = 0;
    root -> danger = 0;
    memset(root -> next, 0, sizeof(root -> next));
    struct Node * c;
    c = (struct Node *)malloc(sizeof(struct Node));
    if (c == NULL)
    {
        free(root);
        return NULL;
    }
    c -> ch = CR;
    c -> danger = 1;
    memset(c -> next, 0, sizeof(c -> next));
    root -> next[2] = c;

    c = (struct Node *)malloc(sizeof(struct Node));
    if (c == NULL)
    {
        free(root);
        return NULL;
    }
    c -> ch = SB;
    c -> danger = 1;
    memset(c -> next, 0, sizeof(c -> next));
    root -> next[0] = c;


    c = (struct Node *)malloc(sizeof(struct Node));
    if (c == NULL)
    {
        free(root);
        return NULL;
    }
    c -> ch = EB;
    c -> danger = 1;
    memset(c -> next, 0, sizeof(c -> next));
    root -> next[1] = c;

    return root;
}

struct Node * init_root()
{
    struct Node *root;
    root = (struct Node *)malloc(sizeof(struct Node));
    if (root == NULL)
        return NULL;
    root -> ch = 0;
    root -> danger = 1;
    memset(root -> next, 0, sizeof(root -> next));
    return root;
}

int build_by_sql(struct Node * root, MYSQL *conn)
{
    int res;
    MYSQL_RES *res_ptr;
    MYSQL_FIELD *field;
    MYSQL_ROW result_row;
    int row,column;
    int i,j;
    res = mysql_query(conn, "select * from `rule_hl7`;");
    if(res)
    {
        printf(" Error: mysql_query!\n");
        mysql_close(conn);
        exit(1);
    }
    else
    {
        res_ptr = mysql_store_result(conn);
        if(res_ptr)
        {
            column = mysql_num_fields(res_ptr);
            row = mysql_num_rows(res_ptr);
            printf(" find %d row.\n", row);
			//printf(" here \n");
            for(i = 1; i < row + 1; i ++)
            {
                result_row = mysql_fetch_row(res_ptr);
                if(add(root, result_row[1]) == 1)
                    continue;
                else
                {
                    FreeSpace(root);
                    show(__func__, __LINE__ - 5);
                    return 0;
                }
            }
        }
    }
    return 1;
}

int build_by_sql_astm(struct Node * root, MYSQL * conn)
{
	int res;
    MYSQL_RES *res_ptr;
    MYSQL_FIELD *field;
    MYSQL_ROW result_row;
    int row,column;
    int i,j;
    res = mysql_query(conn, "select * from `rule_astm`;");
    if(res)
    {
        printf(" Error: mysql_query!\n");
        mysql_close(conn);
        exit(1);
    }
    else
    {
        res_ptr = mysql_store_result(conn);
        if(res_ptr)
        {
            column = mysql_num_fields(res_ptr);
            row = mysql_num_rows(res_ptr);
            printf(" find %d row.\n", row);
			//printf(" here \n");
            for(i = 1; i < row + 1; i ++)
            {
                result_row = mysql_fetch_row(res_ptr);
				//printf(" here \n");
                if(add(root, result_row[1]) == 1)
                    continue;
                else
                {
                    FreeSpace(root);
                    show(__func__, __LINE__ - 5);
                    return 0;
                }
            }
        }
    }
    return 1;
}

int* build_to_http(MYSQL *conn, int *num)
{
	int res;
    MYSQL_RES *res_ptr;
    MYSQL_FIELD *field;
    MYSQL_ROW result_row;
    int row,column;
    int i,j;
	int *result;
    res = mysql_query(conn, "select * from `rule_http`;");
    if(res)
    {
        printf(" Error: mysql_query!\n");
        mysql_close(conn);
        return NULL;
    }
    else
    {
        res_ptr = mysql_store_result(conn);
        if(res_ptr)
        {
            column = mysql_num_fields(res_ptr);
            row = mysql_num_rows(res_ptr);
            printf(" find %d row.\n", row);
			//printf(" here \n");
            *num = row;
			result = (int *)malloc(sizeof(int) * row);
            for(i = 1; i < row + 1; i ++)
            {
                result_row = mysql_fetch_row(res_ptr);
				*(result + i - 1) = *((int *)(result_row[1]));
            }
        }
		else
			return NULL;
    }
    return result;
}
int* build_to_ftp(MYSQL *conn, int* num)
{
	int res;
    MYSQL_RES *res_ptr;
    MYSQL_FIELD *field;
    MYSQL_ROW result_row;
    int row,column;
    int i,j;
	int *result;
    res = mysql_query(conn, "select * from `rule_ftp`;");
    if(res)
    {
        printf(" Error: mysql_query!\n");
        mysql_close(conn);
        return NULL;
    }
    else
    {
        res_ptr = mysql_store_result(conn);
        if(res_ptr)
        {
            column = mysql_num_fields(res_ptr);
            row = mysql_num_rows(res_ptr);
            printf(" find %d row.\n", row);
			//printf(" here \n");
            *num = row;
			result = (int *)malloc(sizeof(int) * row);
            for(i = 1; i < row + 1; i ++)
            {
                result_row = mysql_fetch_row(res_ptr);
				*(result + i - 1) = *((int *)(result_row[1]));
            }
        }
		else
			return NULL;
    }
    return result;
}

int* build_to_dicom(int *num,  MYSQL *conn)
{
    int res;
    MYSQL_RES *res_ptr;
    MYSQL_FIELD *field;
    MYSQL_ROW result_row;
    int row,column;
    int i,j;
	int *result;
    res = mysql_query(conn, "select * from `rule_dicom`;");
    if(res)
    {
        printf(" Error: mysql_query!\n");
        mysql_close(conn);
        return NULL;
    }
    else
    {
        res_ptr = mysql_store_result(conn);
        
        if(res_ptr)
        {
            column = mysql_num_fields(res_ptr);
            row = mysql_num_rows(res_ptr);
            printf("find %d row.\n", row);
			
			*num = row;
			result = (int *)malloc(sizeof(int) * row);
            for(i = 1; i < row + 1; i ++)
            {
                result_row = mysql_fetch_row(res_ptr);
				*(result + i - 1) = (*result_row[1]) - '0';
				//printf("%d\t%d\t%s\n", *(result + i -1), *(result_row[1]), result_row[1]);
            }
        }
		else 
		{
			return NULL;
		}
    }
    return result;
}

int build_to_dicom_str(struct Node * root,  MYSQL *conn)
{
	int res;
    MYSQL_RES *res_ptr;
    MYSQL_FIELD *field;
    MYSQL_ROW result_row;
    int row,column;
    int i,j;
    res = mysql_query(conn, "select * from `rule_dicom_str`;");
    if(res)
    {
        printf(" Error: mysql_query!\n");
        mysql_close(conn);
        exit(1);
    }
    else
    {
        res_ptr = mysql_store_result(conn);
        if(res_ptr)
        {
            column = mysql_num_fields(res_ptr);
            row = mysql_num_rows(res_ptr);
            printf(" find %d row.\n", row);
			//printf(" here \n");
            for(i = 1; i < row + 1; i ++)
            {
                result_row = mysql_fetch_row(res_ptr);
                if(add(root, result_row[1]) == 1)
                    continue;
                else
                {
                    FreeSpace(root);
                    show(__func__, __LINE__ - 5);
                    return 0;
                }
            }
        }
    }
    return 1;
}

int build(struct Node * root, char ** seg, int size)
{
    for (int i = 0; i < size; i ++)
    {
        if (add(root, *(seg + i)) == 1)
            continue;
        else
        {
            FreeSpace(root);
            printf("%d \n", i);
            show( __func__, __LINE__ - 5);
            return 0;
        }
    }
    return 1;
}

int add(struct Node * root, const char *item)
{
    struct Node * current;
    current = root;
    const char * p;
    p = item;
	//printf("%s \n", p);
	//printf("%d \n", sizeof(p));
    for (int i = 0; i < sizeof(p) && *(p + i) != 0; i ++)
    {
		//printf(" %d  ", i);
        int index;
        index = getIndex(*(p + i));
		//printf("%d  %c \n", *(p + i), *(p + i));
		//printf(" %d  %d\n", *(p + i), index);
        if (index < 0)
        {
            show(__func__, __LINE__ - 4);
            FreeSpace(root);
            return 0;
        }
		
        if (current -> next[index] == NULL)
        {
            struct Node * q;
			//printf("%d  %d \n", index, *(p + i));
            q = (struct Node *)malloc(sizeof(struct Node));
			//printf("%d  %d \n", index, *(p + i));
            if (q == NULL)
            {
                show(__func__, __LINE__ - 4);
                FreeSpace(root);
                return 0;
            }
			
            q -> ch = *(p + i);
            q -> danger = 1;
            memset(q -> next, 0, sizeof(q -> next));
            current -> danger = 0;
            current -> next[index] = q;
            current = q;
			
        }
        else
        {
            current = current -> next[index];
        }
    }
    return 1;
}
int getIndex(char p)
{
    /*int index = 0;
    switch (p)
    {
        case SB:
            return 0;
        case EB:
            return 1;
        case CR:
            return 2;
        default:
            if (p <= '9' && p >= '0')
            {
                return (int)((uint8_t)p - '0') + 3;
            }
            else if(p >= 'A' && p <= 'Z')
            {
                return (int)((uint8_t)p - 'A') + 13;
            }
            return -1;
    }*/
	return (int)((uint8_t)p - 1);
}

int process(struct Node * root, struct rte_mbuf * target)
{
    struct rte_mbuf * mbuf = target;
    int length, current_length;
    length = rte_pktmbuf_pkt_len(target);
    current_length = rte_pktmbuf_data_len(target);
    
    struct Node * current;
    //struct Node * stack[6];
    current = root;
    char *p;
    p = rte_pktmbuf_mtod(target, char *);
    int index = -1;
    //int result_num = 0;
    int offset = 0;
    //int stack_num = 0;
    //printf("\n The first frame size is : %d  and segment size is : %d\n", current_length, length);
    for (int i = 0; i < length; i ++, offset ++)
    {
        if (i >= current_length)
        {
            //printf("\n Jumboframe is true. \n");
            offset = 0;
            mbuf = mbuf -> next;
            current_length += rte_pktmbuf_data_len(mbuf);
            p = rte_pktmbuf_mtod(mbuf, char *);
        }
        index = getIndex(*(p + offset));
        if (index == -1)
        {
            //stack_num = 0;
            current = root;
            continue;
        }

        if (current -> next[index] == NULL)
        {
            current = root;
            continue;
        }
        else
        {
            current = current -> next[index];
        }

        if (current -> danger == 1)
        {
            //result_num ++;
            //current = root;
	        return 1;
        }
    }
    return 0;
}



int process_dicom(struct Node * root, int *num, int size, struct rte_mbuf *target)
{
	struct rte_mbuf * mbuf = target;
    int length, current_length;
    length = rte_pktmbuf_pkt_len(target);
    current_length = rte_pktmbuf_data_len(target);
    struct Node * current;
    current = root;
    char *p;
    p = rte_pktmbuf_mtod(target, char *);
    int index = -1;
    int offset = 0;

	for(int i = 0; current_length > 54 && i < size; i++)
	{
		//printf("%d \n", *(num + i));
		if(*(p + 54) == *(num + i))
		{
			//printf("%d \n", *(p + 54));
			return 1;
		}
	} 
    //printf("\n The first frame size is : %d  and segment size is : %d\n", current_length, length);
    for (int i = 0; i < length; i ++, offset ++)
    {
        if (i >= current_length)
        {
            //printf("\n Jumboframe is true. \n");
            offset = 0;
            mbuf = mbuf -> next;
            current_length += rte_pktmbuf_data_len(mbuf);
            p = rte_pktmbuf_mtod(mbuf, char *);
        }
        index = getIndex(*(p + offset));
        if (index == -1)
        {
            current = root;
            continue;
        }

        if (current -> next[index] == NULL)
        {
            current = root;
            continue;
        }
        else
        {
            current = current -> next[index];
        }

        if (current -> danger == 1)
        {
	        return 1;
        }
    }
    return 0;
}

int process_http(int *num, int size, struct rte_mbuf * target)
{
	struct rte_mbuf * mbuf = target;
    int length, current_length;
    length = rte_pktmbuf_pkt_len(target);
    current_length = rte_pktmbuf_data_len(target);
    char *p;
    p = rte_pktmbuf_mtod(target, char *);
    if (current_length > 59)
	{
		memcpy(ch_trans_int.p, p + 54,sizeof(char) * 4);
		for(int i = 0; i < size; i++)
		{
			if (ch_trans_int.number == *(num + i))
				return 1;
		}
	}
	return 0;
}

int process_ftp(int *num, int size, struct rte_mbuf * target)
{
	struct rte_mbuf * mbuf = target;
	union transfer_rule {
		char character[4];
		int number;
	} pasv1, pasv2;
	memcpy(pasv1.character, "227 ", sizeof(char) * 4);
	memcpy(pasv2.character, "PORT", sizeof(char) * 4);
	// pasv1.character[0] = '2';
	// pasv1.character[1] = '2';
	// pasv1.character[2] = '7';
	// pasv1.character[3] = ' ';
	//pasv2.p = {'P', 'A', 'V', 'S'};
    int length, current_length;
    length = rte_pktmbuf_pkt_len(target);
    current_length = rte_pktmbuf_data_len(target);
    char *p;
    p = rte_pktmbuf_mtod(target, char *);
    if (current_length > 59)
	{
		memcpy(ch_trans_int.p, p + 54,sizeof(char) * 4);
		if (pasv1.number == ch_trans_int.number || pasv2.number == ch_trans_int.number)
			return 1;
		//memcpy(ch_trans_int.p, p + 54,sizeof(char) * 4);
		//if (pasv1.number == ch_trans_int.number)
		//	return Ftp_227(root, target);
		//if (pasv2.number == ch_trans_int.number)
		//	return Ftp_PORT(root, target);
		
		/*for(int i = 0; i < size; i++)
		{
			if (ch_trans_int.number == *(num + i))
				return 1;
		}*/
	}
	return 0;
}
