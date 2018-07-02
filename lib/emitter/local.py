# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import logging
import logging.config
import os
import sys

import json
import lib.constants as c

from lib.emitter.emitter import Emitter


class Local(Emitter):

    def __init__(self):
        super(Local, self).__init__()
        # self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
        #                                       LogCommon.IS_SUBCLASS.format(self.task_name,
        #                                                                    issubclass(AssignTask, Task))))

        default_path = c.YAPT_LOGGER_FILE
        default_level = c.YAPT_LOGGER_LEVEL_INFO
        env_key = 'LOG_CFG'
        path = default_path
        value = os.getenv(env_key, None)

        if value:
            path = value
        if os.path.exists(path):

            with open(path, 'rt') as f:
                config = json.loads(f.read())

            logging.config.dictConfig(config)

        else:
            logging.basicConfig(level=default_level)

        if c.YAPT_LOGGER_LEVEL_INFO == c.conf.EMITTER.Local.LogLevel:
            c.logger = logging.getLogger('YAPT.INFO')
        elif c.YAPT_LOGGER_LEVEL_DEBUG == c.conf.EMITTER.Local.LogLevel:
            c.logger = logging.getLogger('YAPT.DEBUG')
        else:
            print 'Unknow log level in YAPT config file: {0}'.format(c.conf.COMMON.LogLevel)
            sys.exit()

    def emit(self, task_name=None, task_state=None, sample_device=None, grp_cfg=None, shared=None, message=None,
             level=logging.INFO):

        func = getattr(c.logger, level.lower())

        if sample_device is None or sample_device.deviceSerial is None:

            header = '[{0:{1}}][{2:{3}}]'.format(task_name.upper(), c.FIRST_PAD, c.FILL_PAD, c.SECOND_PAD)
            func('{0}{1}'.format(header, message))

        else:
            header = '[{0:{1}}][{2:{3}}]'.format(task_name.upper(), c.FIRST_PAD, sample_device.deviceSerial, c.SECOND_PAD)
            func('{0}[{1}]'.format(header, message))
