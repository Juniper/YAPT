# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc
import lib.constants as c
from lib.processor import BackendClientProcessor


class Service(object):

    def __init__(self, normalizer, svc_cfg):
        self.svc_cfg = svc_cfg
        self.logger = c.logger
        self.normalizer = normalizer
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
