# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import time

from jinja2 import Template

from lib.logmsg import LogAssignTask as logmsg
from lib.logmsg import LogCommon
from lib.tasks.task import Task
import lib.constants as c
from lib.tools import Tools


class AssignTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(AssignTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(AssignTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                              logmsg.ASSIGN_INIT.format(self.sample_device.deviceName)))
        self.sample_device.deviceTasks.taskState[self.task_name] = 'Get policy'
        policy_data = c.SRC.get_fw_policy_by_name(self.sample_device.deviceName)

        if policy_data == c.SRC_RESPONSE_FAILURE:

            self.sample_device.deviceTasks.taskState[self.task_name] = c.SRC_RESPONSE_FAILURE
            self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE

        else:
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Get Device'
            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            device_data = c.SRC.get_device_by_name(self.sample_device.deviceName)

            if device_data == c.SRC_RESPONSE_FAILURE:

                self.sample_device.deviceTasks.taskState[self.task_name] = c.SRC_RESPONSE_FAILURE
                self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE

            else:

                time.sleep(c.conf.JUNOSSPACE.RestTimeout)
                try:
                    with open(c.conf.JUNOSSPACE.TemplateDir + self.grp_cfg.TASKS.Provision.Assign.AssignTemplate, 'r') as file:

                        template = Template(file)
                        BODY = template.render(moid=device_data['moid'])

                except IOError as ioe:
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.ASSIGN_TEMPLATE_FILE_NOK.format(
                                                              self.grp_cfg.TASKS.Provision.Assign.AssignTemplate,
                                                              ioe.message)))
                    self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_FAILED
                    self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE
                    return

                if c.conf.JUNOSSPACE.Version == 'space151':
                    self.sample_device.deviceTasks.taskState[self.task_name] = 'Lock policy'
                    c.SRC.lock_fw_policy(policy_data['pid'])

                time.sleep(c.conf.JUNOSSPACE.RestTimeout)
                self.sample_device.deviceTasks.taskState[self.task_name] = 'Assign policy'
                c.SRC.assign_device(BODY, policy_data['pid'])
                time.sleep(c.conf.JUNOSSPACE.RestTimeout)

                if c.conf.JUNOSSPACE.Version == 'space151':
                    self.sample_device.deviceTasks.taskState[self.task_name] = 'Unlock policy'
                    c.SRC.unlock_fw_policy(policy_data['pid'])
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.ASSIGN_DONE.format(policy_data['pid'],
                                                                                self.sample_device.deviceName)))
                self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_DONE
                self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_DONE

    def post_run_task(self):
        pass
