# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc
import lib.constants as c
from lib.processor import BackendClientProcessor


class Service(object):

    def __init__(self, source_plugin, plugin_cfg):
        self.plugin_cfg = plugin_cfg
        self.logger = c.logger
        self.source_plugin = source_plugin
        self.status = c.SVC_INIT
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)

    @abc.abstractmethod
    def start_service(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def stop_service(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def restart_service(self):
        raise NotImplementedError()
