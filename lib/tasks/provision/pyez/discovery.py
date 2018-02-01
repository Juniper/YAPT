# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogDiscoveryTask as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class DiscoveryTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(DiscoveryTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(DiscoveryTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        if self.grp_cfg.TASKS.Provision.Discovery.Mode == 'Discovery':
            resp = c.SRC.discover_by_space(sample_device=self.sample_device, shared=self.shared)
            if resp == c.TASK_STATE_DONE:
                self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
                Tools.emit_log(task_name=self.task_name,
                               task_state={'taskState': self.task_state,
                                           'taskStateMsg': c.TASK_STATE_MSG_DONE},
                               sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                               shared=self.shared, message=c.TASK_STATE_MSG_DONE,
                               scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)
            elif resp == c.TASK_STATE_FAILED:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=c.TASK_STATE_MSG_FAILED)

        elif self.grp_cfg.TASKS.Provision.Discovery.Mode == 'Configlet':
            resp = c.SRC.discover_by_configlet(sample_device=self.sample_device, shared=self.shared)
            if resp == c.TASK_STATE_DONE:
                self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
                Tools.emit_log(task_name=self.task_name,
                               task_state={'taskState': self.task_state,
                                           'taskStateMsg': c.TASK_STATE_MSG_DONE},
                               sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                               shared=self.shared, message=c.TASK_STATE_MSG_DONE,
                               scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)
            elif resp == c.TASK_STATE_FAILED:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=c.TASK_STATE_MSG_FAILED)
        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                   task_state_message=logmsg.DISCOVERY_MODE_NOK.format(
                                       self.grp_cfg.TASKS.Provision.Discovery.Mode))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.DISCOVERY_MODE_NOK.format(self.grp_cfg.TASKS.Provision.Discovery.Mode))

    def post_run_task(self):
        pass
