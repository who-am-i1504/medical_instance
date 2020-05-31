# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2016 Intel Corporation

include $(RTE_SDK)/mk/rte.vars.mk

ifeq ($(CONFIG_RTE_LIBRTE_PDUMP),y)

APP = dpdk-pdump

CFLAGS += -DALLOW_EXPERIMENTAL_API
CFLAGS += $(WERROR_FLAGS)

# all source are stored in SRCS-y

SRCS-y := rule.c main.c

include $(RTE_SDK)/mk/rte.app.mk

CFLAGS += -I/usr/include/mysql
LDFLAGS += -L/usr/lib/mysql
LDLIBS += -lmysqlclient
LDLIBS += -lconfig
endif
