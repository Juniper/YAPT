# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

from jnpr.junos.utils.config import Config
from jnpr.junos.utils.sw import SW

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogInitTask as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class InitTask(Task):
    CHECK_SCHEMA = True
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

        if self.sample_device.deviceConnection.connected:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message='Processing task dependencies: {0}'.format(
                               self.grp_cfg.TASKS.Provision.Init.Dependencies))

            if self.grp_cfg.TASKS.Provision.Init.Dependencies:

                for dep in self.grp_cfg.TASKS.Provision.Init.Dependencies:
                    task_dep = getattr(self, 'dep_init_{0}'.format(dep.lower()))
                    task_dep()

            self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
            Tools.emit_log(task_name=self.task_name,
                           task_state=self.sample_device.deviceTasks.taskState[self.task_name],
                           sample_device=self.sample_device, grp_cfg=self.grp_cfg, shared=self.shared,
                           message=c.TASK_STATE_MSG_DONE, scope=c.LOGGER_SCOPE_ALL,
                           level=c.LOGGER_LEVEL_INFO)

        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                   task_state_message=logmsg.INIT_DEV_CONN_NOK.format(self.sample_device.deviceSerial))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.INIT_DEV_CONN_NOK.format(self.sample_device.deviceSerial))

    def post_run_task(self):
        pass

    def dep_init_configuration(self):
        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                 'Processing configuration task deps for configuration task'))
        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, logmsg.INIT_EXTEND_CFG))
        self.sample_device.deviceConnection.bind(cu=Config)

    def dep_init_software(self):
        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                 'Processing configuration task deps for software task'))
        # PyEZ facts returns empty 'localre' if NFX JDM is queried. If JCP than fine.
        if not self.sample_device.deviceModel.startswith('NFX'):
            self.logger.info(
                Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, logmsg.INIT_EXTEND_SW))
            self.sample_device.deviceConnection.bind(sw=SW)

        else:
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.INIT_EXTEND_SW_NOK))
