# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import logging
import logging.config
import os

import yaml
import lib.constants as c

from lib.emitter.emitter import Emitter


class Local(Emitter):

    def __init__(self):
        super(Local, self).__init__()
        # self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
        #                                       LogCommon.IS_SUBCLASS.format(self.task_name,
        #                                                                    issubclass(AssignTask, Task))))

        default_path = c.YAPT_LOGGER_FILE
        default_level = c.YAPT_LOGGER_LEVEL
        env_key = 'LOG_CFG'
        c.logger = logging.getLogger('YAPT')
        path = default_path
        value = os.getenv(env_key, None)

        if value:
            path = value
        if os.path.exists(path):

            with open(path, 'rt') as f:
                config = yaml.load(f.read())
            logging.config.dictConfig(config)
            # emitter.getLogger("pika").setLevel(emitter.WARNING)
            # emitter.getLogger("requests").setLevel(emitter.WARNING)
            logging.getLogger("pika").propagate = False
            logging.getLogger("requests").propagate = False
            logging.getLogger("ncclient").propagate = False
            logging.getLogger("paramiko").propagate = False
            logging.getLogger("ws4py").propagate = False

        else:
            logging.basicConfig(level=default_level)

    def emit(self, task_name=None, task_state=None, sample_device=None, grp_cfg=None, shared=None, message=None, level=logging.INFO):

        func = getattr(c.logger, level.lower())

        if sample_device is None or sample_device.deviceSerial is None:

            header = '{0:{1}}{2:{3}}'.format(task_name.upper(), c.FIRST_PAD, c.FILL_PAD, c.SECOND_PAD)
            func('{0}{1}'.format(header, message))

        else:
            header = '{0:{1}}{2:{3}}'.format(task_name.upper(), c.FIRST_PAD, sample_device.deviceSerial, c.SECOND_PAD)
            func('{0}{1}'.format(header, message))
