# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogInitTask as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class InitTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(InitTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(InitTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        if self.sample_device.deviceConnection is not None:
            self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
            Tools.emit_log(task_name=self.task_name,
                           task_state={'taskState': self.task_state,
                                       'taskStateMsg': c.TASK_STATE_MSG_DONE},
                           sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                           shared=self.shared, message=c.TASK_STATE_MSG_DONE,
                           scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)

        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                   task_state_message=logmsg.INIT_DEV_CONN_NOK.format(self.sample_device.deviceIP))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.INIT_DEV_CONN_NOK.format(self.sample_device.deviceIP))

    def post_run_task(self):
        pass
