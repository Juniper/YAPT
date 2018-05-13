# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


from ncclient.operations import TimeoutExpiredError

import lib.constants as c
from lib.logmsg import LogCleanupTask as logmsg
from lib.logmsg import LogCommon
from lib.tasks.task import Task
from lib.tools import Tools


class CleanupTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(CleanupTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(CleanupTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                 logmsg.CLEANUP_CLOSE_CONN.format(hex(id(self.sample_device.deviceConnection)))))

        try:
            self.sample_device.deviceConnection.close()
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.CLEANUP_CLOSE_CONN_SUCCESS.format(
                                                      hex(id(self.sample_device.deviceConnection)))))

        except TimeoutExpiredError:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message='Connection timeout error')
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message='Connection timeout error')
            return

        self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
        Tools.emit_log(task_name=self.task_name,
                       task_state={'taskState': self.task_state,
                                   'taskStateMsg': c.TASK_STATE_MSG_DONE},
                       sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                       shared=self.shared, message=c.TASK_STATE_MSG_DONE,
                       scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)

    def post_run_task(self):
        pass
