# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import argparse
import lib.constants as c
from lib.processor import TaskProcessor
from lib.processor import ServiceProcessor
from lib.pluginfactory import EmitterPlgFact
from lib.pluginfactory import SpacePluginFactory
from lib.factories import FactoryContainer
from lib.tools import Tools


class YaptSvc(object):

    if __name__ == '__main__':

        Tools.create_config_view(c.CONFIG_TYPE_MAIN)
        EmitterPlgFact()

        parser = argparse.ArgumentParser()
        parser.add_argument("amqpIp", help="provide amqp bus ip")
        args = parser.parse_args()
        c.conf.AMQP.Host = args.amqpIp

        c.fc = FactoryContainer().get_factory_container()
        c.taskq = c.fc.taskq()

        if c.conf.JUNOSSPACE.Enabled:
            spf = SpacePluginFactory(c.conf.JUNOSSPACE.Version)
            c.SRC = spf.init_plugin()

        for item in range(c.conf.YAPT.WorkerThreads):
            taskprocessor = TaskProcessor(target=TaskProcessor, name=c.AMQP_PROCESSOR_TASK + str(item),
                                          args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type, c.AMQP_PROCESSOR_TASK,
                                                c.AMQP_PROCESSOR_TASK,))
            taskprocessor.start()

        serviceprocessor = ServiceProcessor(target=ServiceProcessor, name=c.AMQP_PROCESSOR_SVC,
                                            args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type,
                                                  c.AMQP_PROCESSOR_SVC,
                                                  c.AMQP_PROCESSOR_SVC,))
        serviceprocessor.start()
