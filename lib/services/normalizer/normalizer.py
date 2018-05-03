# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc

from lib.processor import ClientProcessor
import lib.constants as c


class Normalizer(object):
    def __init__(self, svc_cfg=None):
        self.logger = c.logger
        self.svc_cfg = svc_cfg
        self.amqpCl = ClientProcessor(exchange=c.conf.AMQP.Exchange, routing_key=c.AMQP_PROCESSOR_TASK,
                                      queue=c.AMQP_PROCESSOR_TASK)

    @abc.abstractmethod
    def pre_run_normalizer(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def run_normalizer(self, timestamp):
        raise NotImplementedError()

    @abc.abstractmethod
    def post_run_normalizer(self):
        raise NotImplementedError()

    def send_message(self, message):
        self.amqpCl.send_message(message=message)
