# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc

from lib.processor import ClientProcessor
import lib.constants as c


class SourcePlugin(object):
    def __init__(self, plugin_cfg=None):
        self.logger = c.logger
        self.plugin_cfg = plugin_cfg
        self.amqpCl = ClientProcessor(exchange=c.conf.AMQP.Exchange, routing_key=c.AMQP_PROCESSOR_TASK,
                                      queue=c.AMQP_PROCESSOR_TASK)

    @abc.abstractmethod
    def pre_run_source_plugin(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def run_source_plugin(self, timestamp):
        raise NotImplementedError()

    @abc.abstractmethod
    def post_run_source_plugin(self):
        raise NotImplementedError()

    def send_message(self, message):
        self.amqpCl.send_message(message=message)
