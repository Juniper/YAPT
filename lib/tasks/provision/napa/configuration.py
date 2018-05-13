# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


from napalm_base.exceptions import MergeConfigException
from napalm_base.exceptions import ReplaceConfigException

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogConfigurationTask as logmsg
from lib.tasks.task import Task
from lib.tasks.tasktools import Configuration
from lib.tools import Tools


class ConfigurationTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(ConfigurationTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(ConfigurationTask, Task))))
        self._device_config_file = None

    def pre_run_task(self):
        pass

    def run_task(self):

        """
        Provision device config

        :param sample_device: A device object for which the config provisioning should be done
        :return:
        """
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                              logmsg.CONF_TASK_INIT.format(format(self.sample_device.deviceSerial))))
        configurator = Configuration()
        resp = configurator.prepare_device_config(sample_device=self.sample_device)
        self._device_config_file = resp['configfilename']

        if self.sample_device.deviceConnection is not None:

            self.sample_device.deviceConnection.load_replace_candidate(
                filename=self.grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + self._device_config_file)
            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message=logmsg.CONF_TASK_COMMIT)
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=logmsg.CONF_TASK_COMMIT)

            # Todo: Check Exception
            try:
                self.sample_device.deviceConnection.commit_config()
                self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
                Tools.emit_log(task_name=self.task_name,
                               task_state={'taskState': self.task_state,
                                           'taskStateMsg': c.TASK_STATE_MSG_DONE},
                               sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                               shared=self.shared, message=logmsg.CONF_TASK_COMMIT_OK.format(self._device_config_file),
                               scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)

            except (ReplaceConfigException, MergeConfigException) as err:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.CONF_TASK_COMMIT_NOK.format(err))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_COMMIT_NOK.format(err))
            return

        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                   task_state_message=logmsg.CONF_TASK_CONN_NOK.format(self.sample_device.deviceIP))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.CONF_TASK_CONN_NOK.format(self.sample_device.deviceIP))
            return

    def post_run_task(self):
        pass
