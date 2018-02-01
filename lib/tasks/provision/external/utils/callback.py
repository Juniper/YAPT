# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible.plugins.callback import CallbackBase
from lib.logmsg import LogAnsibleTask as logmsg
import lib.constants as c
from lib.tools import Tools


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'amqp_and_yapt_log'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self, sample_device=None, shared=None):

        super(CallbackModule, self).__init__()
        self.logger = c.logger
        self.sample_device = sample_device
        self.shared = shared

    def v2_runner_on_failed(self, res, ignore_errors=False):
        self.logger.info(Tools.create_log_msg(logmsg.ANSIBLEAPI, self.sample_device.deviceSerial,
                                              logmsg.PLAYBOOK_TASK_ERROR.format(res._task.get_name())))
        self.sample_device.deviceTasks.taskState['Ansibleapi'] = res._task.get_name()
        self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE
        return

    def v2_runner_on_ok(self, res):
        self.logger.info(Tools.create_log_msg(logmsg.ANSIBLEAPI, self.sample_device.deviceSerial,
                                              logmsg.PLAYBOOK_TASK_OK.format(res._task.get_name())))
        self.sample_device.deviceTasks.taskState['Ansibleapi'] = res._task.get_name()

    def v2_runner_on_skipped(self, host, item=None):
        pass

    def v2_runner_on_unreachable(self, res):
        self.logger.info(Tools.create_log_msg(logmsg.ANSIBLEAPI, self.sample_device.deviceSerial,
                                              logmsg.ERROR_UNREACHABLE.format(res._task.get_name())))
        self.sample_device.deviceTasks.taskState['Ansibleapi'] = res._task.get_name()
        self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE

    def v2_runner_on_async_failed(self, res):
        pass

    def v2_runner_retry(self, result):
        pass

    def v2_playbook_on_start(self, playbook):
        pass

    def v2_playbook_on_import_for_host(self, res, imported_file):
        pass

    def v2_playbook_on_not_import_for_host(self, res, missing_file):
        pass
