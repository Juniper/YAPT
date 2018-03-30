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

    def __init__(self, sample_device=None, shared=None, update_task_state=None):

        super(CallbackModule, self).__init__()
        self.logger = c.logger
        self.sample_device = sample_device
        self.shared = shared
        self.update_task_state = update_task_state
        self.task_name = 'Ansibleapi'

    def v2_runner_on_failed(self, res, ignore_errors=False):
        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                               task_state_message=res._task.get_name())
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.PLAYBOOK_ERROR.format(res._task.get_name()))
        return

    def v2_runner_on_ok(self, res):
        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                               task_state_message=res._task.get_name())
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.PLAYBOOK_TASK_OK.format(res._task.get_name()))

    def v2_runner_on_skipped(self, host, item=None):
        pass

    def v2_runner_on_unreachable(self, res):
        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                               task_state_message=res._task.get_name())
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.ERROR_UNREACHABLE.format(res._task.get_name()))

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
