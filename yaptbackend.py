# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import argparse

from lib.backend.backend import Backend
import lib.constants as c
from lib.pluginfactory import BackendPluginFactory
from lib.pluginfactory import EmitterPlgFact
from lib.tools import Tools


class YaptBackend(object):

    if __name__ == '__main__':

        Tools.create_config_view('main')
        EmitterPlgFact()

        parser = argparse.ArgumentParser()
        parser.add_argument("amqpIp", help="provide amqp bus ip")
        args = parser.parse_args()
        c.conf.AMQP.Host = args.amqpIp

        BackendPluginFactory(plugin_name=c.conf.BACKEND.Module, target=Backend,
                             name=c.AMQP_PROCESSOR_BACKEND)
