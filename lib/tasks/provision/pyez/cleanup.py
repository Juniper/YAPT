# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import lib.constants as c

from jnpr.junos.exception import ConnectClosedError
from napalm_base.base import NetworkDriver
from ncclient.operations import TimeoutExpiredError

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
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.CLEANUP_CLOSE_CONN.format(
                           hex(id(self.sample_device.deviceConnection))))

        if isinstance(self.sample_device.deviceConnection, NetworkDriver):
            self.sample_device.deviceConnection.close()

        else:
            if c.SOURCEPLUGIN_OSSH in self.sample_device.deviceSourcePlugin:

                try:
                    self.sample_device.deviceConnection.cli('op cleanup', warning=False)

                except ConnectClosedError as cce:
                    pass

                c.oss_seen_devices_lck.acquire()

                try:
                    if self.sample_device.deviceIP in c.oss_seen_devices:
                        c.oss_seen_devices.pop(self.sample_device.deviceIP, None)
                finally:
                    c.oss_seen_devices_lck.release()
                    self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
                    Tools.emit_log(task_name=self.task_name,
                                   task_state=self.sample_device.deviceTasks.taskState[self.task_name],
                                   sample_device=self.sample_device, grp_cfg=self.grp_cfg, shared=self.shared,
                                   message=logmsg.CLEANUP_CLOSE_CONN_SUCCESS.format(
                                       hex(id(self.sample_device.deviceConnection))), scope=c.LOGGER_SCOPE_ALL,
                                   level=c.LOGGER_LEVEL_INFO)
            else:

                if self.sample_device.deviceConnection.connected:

                    try:
                        self.sample_device.deviceConnection.close()
                        self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                               task_state_message=c.TASK_STATE_MSG_DONE)
                        Tools.emit_log(task_name=self.task_name,
                                       task_state=self.sample_device.deviceTasks.taskState[self.task_name],
                                       sample_device=self.sample_device, grp_cfg=self.grp_cfg, shared=self.shared,
                                       message=logmsg.CLEANUP_CLOSE_CONN_SUCCESS.format(
                                           hex(id(self.sample_device.deviceConnection))), scope=c.LOGGER_SCOPE_ALL,
                                       level=c.LOGGER_LEVEL_INFO)

                    except TimeoutExpiredError:
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=logmsg.CLEANUP_CLOSE_CONN_TIMEOUT)
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CLEANUP_CLOSE_CONN_TIMEOUT)

                        return

                else:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.CLEANUP_CLOSE_CONN_ERROR.format(
                                               hex(id(self.sample_device.deviceConnection))))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CLEANUP_CLOSE_CONN_ERROR.format(
                                       hex(id(self.sample_device.deviceConnection))))

                    return

    def post_run_task(self):
        pass
