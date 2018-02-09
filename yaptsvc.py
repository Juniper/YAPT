# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import argparse
from lib.processor import TaskProcessor
from lib.processor import ServiceProcessor
from lib.pluginfactory import EmitterPlgFact
from lib.pluginfactory import SpacePluginFactory
import lib.constants as c
from lib.tools import Tools


class YaptSvc(object):

    if __name__ == '__main__':

        Tools.create_config_view('main')
        EmitterPlgFact()

        parser = argparse.ArgumentParser()
        parser.add_argument("amqpIp", help="provide amqp bus ip")
        args = parser.parse_args()
        c.conf.AMQP.Host = args.amqpIp

        if c.conf.JUNOSSPACE.Enabled:
            spf = SpacePluginFactory(c.conf.JUNOSSPACE.Version)
            c.SRC = spf.init_plugin()

        for item in range(c.conf.YAPT.WorkerThreads):
            taskprocessor = TaskProcessor(target=TaskProcessor, name=c.AMQP_PROCESSOR_TASK + str(item),
                                          args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type, c.AMQP_PROCESSOR_TASK,
                                                c.AMQP_PROCESSOR_TASK,))
            taskprocessor.start()

        serviceprocessor = ServiceProcessor(target=ServiceProcessor, name=c.AMQP_PROCESSOR_SERVICE,
                                            args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type,
                                                  c.AMQP_PROCESSOR_SERVICE,
                                                  c.AMQP_PROCESSOR_SERVICE,))
        serviceprocessor.start()
