# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import multiprocessing
import argparse
from lib.web.ui import UiProcessor
import lib.constants as c
from lib.tools import Tools
from lib.web.base import UiInit
from lib.pluginfactory import EmitterPlgFact


class YaptUi(object):

    if __name__ == '__main__':

        Tools.create_config_view(c.CONFIG_TYPE_MAIN)
        EmitterPlgFact()

        parser = argparse.ArgumentParser()
        parser.add_argument("amqpIp", help="provide amqp bus ip")
        args = parser.parse_args()
        c.conf.AMQP.Host = args.amqpIp

        uiprocessor = UiProcessor(target=UiProcessor, name=c.AMQP_PROCESSOR_UI, args=(
            c.conf.AMQP.Exchange, c.conf.AMQP.Type, c.AMQP_PROCESSOR_UI, c.AMQP_PROCESSOR_UI,))
        uiprocessor.start()

        p = multiprocessing.Process(target=UiInit, args=())
        p.start()
