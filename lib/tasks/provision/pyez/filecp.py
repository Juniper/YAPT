# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import paramiko
from jnpr.junos.utils.scp import SCP
from scp import SCPClient

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogFilecpTask as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class FilecpTask(Task):
    """
    filecp copies given file(s) to device.

    :param sample_device: A device object to copy the file to
    :param file: the file names to copy
    :param remote_path: the remote path on the device
    :return:
    """

    CHECK_SCHEMA = True
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(FilecpTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(FilecpTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.CP_INIT.format(self.grp_cfg.TASKS.Provision.Filecp.Files))

        if self.sample_device.deviceConnection.connected:

            try:
                if c.SERVICEPLUGIN_OSSH == self.sample_device.deviceServicePlugin:
                    with SCPClient(self.sample_device.deviceConnection._conn._session.transport) as scp:
                        for _file in self.grp_cfg.TASKS.Provision.Filecp.Files:
                            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                                   task_state_message=logmsg.CP_COPY.format(_file))
                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=logmsg.CP_COPY.format(_file))
                            scp.put(self.grp_cfg.TASKS.Provision.Filecp.FileLocalDir + _file,
                                    self.grp_cfg.TASKS.Provision.Filecp.FileRemoteDir)
                            Tools.emit_log(task_name=self.task_name, task_state={'taskState': self.task_state,
                                                                                 'taskStateMsg': c.TASK_STATE_MSG_DONE},
                                           sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                           shared=self.shared,
                                           message=logmsg.CP_SUCCESS.format(_file), scope=c.LOGGER_SCOPE_ALL,
                                           level=c.LOGGER_LEVEL_INFO)
                            self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                                   task_state_message=c.TASK_STATE_MSG_DONE)
                else:
                    with SCP(self.sample_device.deviceConnection, progress=False) as scp:
                        for _file in self.grp_cfg.TASKS.Provision.Filecp.Files:
                            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                                   task_state_message=logmsg.CP_COPY.format(_file))
                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=logmsg.CP_COPY.format(_file))
                            scp.put(self.grp_cfg.TASKS.Provision.Filecp.FileLocalDir + _file,
                                    self.grp_cfg.TASKS.Provision.Filecp.FileRemoteDir)
                            Tools.emit_log(task_name=self.task_name, task_state={'taskState': self.task_state,
                                                                                 'taskStateMsg': c.TASK_STATE_MSG_DONE},
                                           sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                           shared=self.shared,
                                           message=logmsg.CP_SUCCESS.format(_file), scope=c.LOGGER_SCOPE_ALL,
                                           level=c.LOGGER_LEVEL_INFO)
                            self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                                   task_state_message=c.TASK_STATE_MSG_DONE)

            except (paramiko.BadHostKeyException, paramiko.AuthenticationException)as e:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CP_FAILED.format(e.message))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.CP_FAILED.format(e.message))
        else:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=logmsg.CP_FAILED_NO_CONN)
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=logmsg.CP_FAILED_NO_CONN)

    def post_run_task(self):
        pass
