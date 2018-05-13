# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import lib.constants as c

from lib.logmsg import LogCommon
from lib.logmsg import Logipam as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class NetboxTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0
    TASK_DESCENT = 'Ipam'

    def __init__(self, sample_device=None, shared=None):

        super(NetboxTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(NetboxTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        pass

    def post_run_task(self):
        pass