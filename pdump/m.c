#include "capture.h"

static void
signal_handler(int sig_num)
{
	if (sig_num == SIGINT) {
		printf("\n\nSignal %d received, preparing to exit...\n",
				sig_num);
		quit_signal = 1;
	}
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

	stats->dequeue_pkts += nb_in_deq;
    //printf("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b %"PRIu64"\t", stats->dequeue_pkts);

	if (nb_in_deq) {
		/* then sent on vdev */
        //此处为筛选逻辑
        char *current_data;
        for(int i = 0; i < nb_in_deq; i ++)
        {
			if (rte_pktmbuf_data_len(rxtx_bufs[i])<=DST_PORT + 1)
				continue;
            current_data = rte_pktmbuf_mtod(rxtx_bufs[i], char *);
			if (*(current_data + TCP_TAG) != TCP_TAG_VALUE){
				rte_pktmbuf_free(rxtx_bufs[i]);
				continue;
			}
			if (p->port != 0)
            {
            	src_port.p[0] = *(current_data + SRC_PORT + 1);
            	src_port.p[1] = *(current_data + SRC_PORT);
            	dst_port.p[0] = *(current_data + DST_PORT + 1);
            	dst_port.p[1] = *(current_data + DST_PORT);
			}
            if (p->port == 0 || p->port == src_port.port || p->port == dst_port.port)
            {
                 if(p->dir & ENABLE_HTTP)
				{
					if (ProcessAll(http_root, rxtx_bufs[i]) > 0)
					{
						struct rte_mbuf *s;
						struct rte_mbuf *last;
						s = rxtx_bufs[i];
						bufs_http[clone_size_http] = rte_pktmbuf_clone(s, clone_pool);
						last = bufs_http[clone_size_http];
						s = s -> next;
						while(s != NULL)
						{
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
						if (AddInListFtp(ftp_root, rxtx_bufs[i])==1);
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
						if (AddInList(dicom_root, rxtx_bufs[i]) > 0)
						{
							
							struct rte_mbuf *s;
							struct rte_mbuf *last;
							s = rxtx_bufs[i];
							bufs_dicom[clone_size_dicom] = rte_pktmbuf_clone(s, clone_pool);
							last = bufs_dicom[clone_size_dicom];
							s = s -> next;
							while(s != NULL)
							{
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
    for (i = 0; i < num_tuples; i++)
    {
        pt = &pdump_t[i];
        if (rte_eth_dev_socket_id(pt->device_id) > 0 &&
              rte_eth_dev_socket_id(pt->device_id) != (int)rte_socket_id())
            printf("WARNING, port %u is on remote NUMA node to polling thread.\n\t Performance will not be optimal.\n", pt->device_id);
    }

	while (!quit_signal) {
		current_time = (time(NULL) - start_time) / 60;
		for (i = 0; i < num_tuples; i++) {
			if (current_time >= pt -> time)
				goto save_result;
			pt = &pdump_t[i];
			struct rte_mbuf *bufs[BURST_SIZE];
			const uint16_t nb_rx = rte_eth_rx_burst(pt->device_id, 0,
					bufs, BURST_SIZE);
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

int initHL7(const char * value)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (value == NULL){
        pt->dir = (pt->dir & DISABLE_HL7);
        FreeSpace(root);
        FreeList(hl7_root);
        return 0;
    }
    // HL7 tag
    pt->dir = (pt->dir | ENABLE_HL7);
    // HL7 pcap path
    
    snprintf(pt->hl7_dev, sizeof(pt->hl7_dev), "%s", value);
    // init HL7 dictornary tree
    root = init_root();
    MYSQL * conn = init_sql();
    // build HL7 dictornary tree
    int tag = build_by_sql(root, conn);
    if(tag < 0)
    {
        printf(" Error in conduct hl7 rule tree.\n");
        end_software();
        return -1;
    }
    // init HL7 IP LinkList
    hl7_root = initList();
    mysql_close(conn);
    return 0;
}

int initDICOM(const char * value)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (value == NULL){
        pt->dir = (pt->dir & DISABLE_DICOM);
        FreeSpace(root_dicom);
        free(dicom_rule);
        FreeList(dicom_root);
        return 0;
    }
    // DICOM tag
    pt->dir = (pt->dir | ENABLE_DICOM);
    // DICOM pcap path
    snprintf(pt->dicom_dev, sizeof(pt->dicom_dev), "%s", value);
    // init DICOM dictornary tree
    root_dicom = init_root();
    MYSQL * conn = init_sql();
    // build DICOM dictornary tree
    dicom_rule = build_to_dicom(&dicom_size, conn);
    int tag = build_to_dicom_str(root_dicom, conn);
    if(dicom_rule == NULL || tag < 0)
    {
        printf(" Error in conduct DICOM rule tree.\n");
        end_software();
        return -1;
    }
    // init DICOM IP LinkList
    dicom_root = initList();
    mysql_close(conn);
    return 0;
}

int initASTM(const char * value)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (value == NULL){
        pt->dir = (pt->dir & DISABLE_ASTM);
        FreeSpace(root_astm);
        FreeList(astm_root);
        return 0;
    }
    // ASTM tag
    pt->dir = (pt->dir | ENABLE_ASTM);
    // ASTM pcap path
    snprintf(pt->astm_dev, sizeof(pt->astm_dev), "%s", value);
    // init ASTM dictornary tree
    root_astm = init_root();
    MYSQL * conn = init_sql();
    // build ASTM dictornary tree
    int tag = build_by_sql_astm(root_astm, conn);
    if(tag < 0)
    {
        printf(" Error in conduct ASTM rule tree.\n");
        end_software();
        return -1;
    }
    // init ASTM IP LinkList
    astm_root = initList();
    mysql_close(conn);
    return 0;
}

int initHTTP(const char * value)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (value == NULL){
        pt->dir = (pt->dir & DISABLE_HTTP);
        free(http_rule);
        FreeList(http_root);
        return 0;
    }
    // HTTP tag
    pt->dir = (pt->dir | ENABLE_HTTP);
    // HTTP pcap path
    snprintf(pt->http_dev, sizeof(pt->http_dev), "%s", value);
    MYSQL * conn = init_sql();
    // build HTTP dictornary tree
    http_rule = build_to_http(conn, &http_size);
    if(http_rule == NULL)
    {
        printf(" Error in conduct HTTP rule.\n");
        end_software();
        return -1;
    }
    // init HTTP IP LinkList
    http_root = initList();
    mysql_close(conn);
    return 0;
}

int initFTP(const char * value)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (value == NULL){
        pt->dir = (pt->dir & DISABLE_FTP);
        free(ftp_rule);
        FreeList(ftp_root);
        return 0;
    }
    // FTP tag
    pt->dir = (pt->dir | ENABLE_FTP);
    // FTP pcap path
    snprintf(pt->ftp_dev, sizeof(pt->ftp_dev), "%s", value);
    MYSQL * conn = init_sql();
    // build FTP dictornary tree
    ftp_rule = build_to_ftp(conn, &ftp_size);
    if(ftp_rule == NULL)
    {
        printf(" Error in conduct HTTP rule.\n");
        end_software();
        return -1;
    }
    // init FTP IP LinkList
    ftp_root = initList();
    mysql_close(conn);
    return 0;
}

int initPort(int port)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (port >= 0 && port <= 65535)
    {
        pt->port = (uint16_t)port;
        return 0;
    }
    printf("Please check the port value is not in 1 ~ 65535");
    return -1;
}

int initDevice(int device_id)
{
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (device_id < 0)
    {
        printf("the device_id is not suitable.");
        return -1;
    }
    pt->device_id = (uint16_t)device_id;
    return 0;
}

void end_software(void)
{
    struct pdump_tuples *pt;
    for (int i = 0; i < num_tuples; i++)
    {
        pt = &pdump_t[i];
    
        if (pt->dir & ENABLE_HL7)
        {
            pt->dir = (pt->dir & DISABLE_HL7);
            FreeSpace(root);
            FreeList(hl7_root);
        }
        if (pt->dir & ENABLE_DICOM)
        {
            pt->dir = (pt->dir & DISABLE_DICOM);
            FreeSpace(root_dicom);
            free(dicom_rule);
            FreeList(dicom_root);
        }
        if (pt->dir & ENABLE_ASTM)
        {
            pt->dir = (pt->dir & DISABLE_ASTM);
            FreeSpace(root_astm);
            FreeList(astm_root);
        }
        if (pt->dir & ENABLE_HTTP)
        {
            pt->dir = (pt->dir & DISABLE_HTTP);
            free(http_rule);
            FreeList(http_root);
        }
        if (pt->dir & ENABLE_FTP)
        {
            pt->dir = (pt->dir & DISABLE_FTP);
            free(ftp_rule);
            FreeList(ftp_root);
        }
    }
    cleanup_pdump_resources();
    print_pdump_stats();
    int ret = rte_eal_cleanup();
    if(ret)
        printf("Error from rte_eal_cleanup(), %d\n", ret);
    num_tuples = 0;
}

void start_capture(char *c_flag, char * n_flag)
{
    signal(SIGINT, signal_handler);
    int argc = 3;
    char *argp[argc];
    argp[0] = "EAL";
    if (c_flag !=NULL)
    {
        argp[1] = c_flag;
    }
    else
    {
        argp[1] = "-c1";
    }
    if (n_flag !=NULL)
    {
        argp[2] = n_flag;
    }
    else
    {
        argp[2] = "-n4";
    }
    int ret = rte_eal_init(argc, argp);
    if (ret < 0)
        rte_panic("Cannot init EAL\n");
    if (rte_eth_dev_count_avail() == 0)
        rte_exit(EXIT_FAILURE, "No Ethernet ports - bye\n");
    create_mp_ring_vdev();
    dump_packets();
    end_software();
}
// 0 means use the default params value
int initParams(int MSIZE, int MBUFS, uint64_t capture_time)
{
    if (MSIZE < 0 || MSIZE > UINT16_MAX || (MBUFS < 1025 && MBUFS != 0) || MBUFS > UINT16_MAX)
    {
        printf(" The MSIZE between 1 ~ UINT16_MAX.\n");
        printf(" The MBUFS between 1025 ~ UINT16_MAX.\n");
        return -1;
    }
    struct pdump_tuples *pt;
    pt = &pdump_t[num_tuples];
    if (MSIZE == 0)
    {
        pt->mbuf_data_size = RTE_MBUF_DEFAULT_BUF_SIZE;
    }
    else
    {
        pt->mbuf_data_size = (uint16_t)MSIZE;
    }
    if (MBUFS == 0)
    {
        pt->total_num_mbufs = MBUFS_PER_POOL;
    }
    else
    {
        pt->total_num_mbufs = (uint16_t) MBUFS;
    }
    if (capture_time == 0)
    {
        pt -> time = 10;
    }
    else
    {
        pt -> time = capture_time;
    }
    num_tuples ++;
    return 0;
}