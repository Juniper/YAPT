# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import lib.constants as c
import multiprocessing

from lib.pluginfactory import EmitterPlgFact
from lib.factories import FactoryContainer
from lib.backend.backend import Backend
from lib.pluginfactory import BackendPluginFactory
from lib.processor import TaskProcessor
from lib.processor import ServiceProcessor
from lib.web.ui import UiProcessor
from lib.pluginfactory import SpacePluginFactory
from lib.tools import Tools
from lib.web.base import UiInit


class Yapt(object):
    if __name__ == '__main__':

        Tools.create_config_view(c.CONFIG_TYPE_MAIN)
        EmitterPlgFact()

        uiprocessor = UiProcessor(target=UiProcessor, name=c.AMQP_PROCESSOR_UI, args=(
            c.conf.AMQP.Exchange, c.conf.AMQP.Type, c.AMQP_PROCESSOR_UI, c.AMQP_PROCESSOR_UI,))
        uiprocessor.start()

        #multiprocessing.set_start_method('spawn')
        p = multiprocessing.Process(target=UiInit, args=())
        p.start()

        c.fc = FactoryContainer().get_factory_container()
        c.taskq = c.fc.taskq()

        BackendPluginFactory(plugin_name=c.conf.BACKEND.Module, target=Backend,
                             name=c.AMQP_PROCESSOR_BACKEND)

        for item in range(c.conf.COMMON.WorkerThreads):
            taskprocessor = TaskProcessor(target=TaskProcessor, name=c.AMQP_PROCESSOR_TASK + str(item),
                                          args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type, c.AMQP_PROCESSOR_TASK,
                                                c.AMQP_PROCESSOR_TASK,))
            taskprocessor.start()

        if c.conf.JUNOSSPACE.Enabled:
            spf = SpacePluginFactory(c.conf.JUNOSSPACE.Version)
            c.SRC = spf.init_plugin()

        serviceprocessor = ServiceProcessor(target=ServiceProcessor, name=c.AMQP_PROCESSOR_SVC,
                                            args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type, c.AMQP_RPC_SERVICE_QUEUE,))
        serviceprocessor.start()
