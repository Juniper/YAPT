# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


import time

from jinja2 import Template

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogPolicyTask as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class PolicyTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(PolicyTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(PolicyTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                              logmsg.POLICY_INIT.format(self.sample_device.deviceName)))

        try:
            with open(c.conf.JUNOSSPACE.TemplateDir + self.grp_cfg.TASKS.Provision.Policy.PolicyTemplate, 'r') as f:
                template = Template(f)
                BODY = template.render(name=self.sample_device.deviceName,
                                       type=self.grp_cfg.TASKS.Provision.Policy.LookupType)
                response = c.SRC.add_fw_policy(BODY)

        except IOError as ioe:

            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.POLICY_TEMP_FILE_NOK.format(
                                                      self.grp_cfg.TASKS.Provision.Policy.PolicyTemplate, ioe.message)))
            self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_FAILED
            self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE
            return

        if response.status_code == 500:
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.POLICY_CREATE_NOK.format(self.sample_device.deviceName,
                                                                                  response.status_code, response.text)))
            self.sample_device.deviceTasks.taskState[self.task_name] = response.text
            self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE

        elif response.status_code == 200:

            self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_DONE
            self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_DONE
            time.sleep(c.conf.JUNOSSPACE.RestTimeout)

        else:
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.POLICY_UNKNOWN_CODE.format(response.status_code)))

    def post_run_task(self):
        pass
