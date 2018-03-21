# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import lib.constants as c

from lib.logmsg import LogCommon
from lib.tasks.task import Task
from lib.tools import Tools


class MyOwnTask(Task):
    CHECK_SCHEMA = True
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):
        super(MyOwnTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(MyOwnTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, 'My first own task'))

    def post_run_task(self):
        pass
