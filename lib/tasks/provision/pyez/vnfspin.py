# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import Logvnfspin as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class VnfspinTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(VnfspinTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(VnfspinTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        # this task has to run some when after configuration task
        # Spin up VNFs
        # Done

        datavars = self.sample_device.deviceConfigData

        if datavars:
            for vnf in datavars['device']['vnfs']:
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.VNFSPIN_INIT.format(vnf['name'])))
                req1 = '{0} {1}'.format('request virtual-network-functions start', vnf['name'])
                self.sample_device.deviceConnection.cli(command=req1, format='text', warning=False)
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.VNFSPIN_VNF_OK.format(vnf['name']))
                Tools.emit_log(task_name=self.task_name, task_state={'taskState': self.task_state,
                                                                     'taskStateMsg': c.TASK_STATE_MSG_DONE},
                               sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                               shared=self.shared,
                               message=logmsg.VNFSPIN_VNF_OK.format(vnf['name']), scope=c.LOGGER_SCOPE_ALL,
                               level=c.LOGGER_LEVEL_INFO)
        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=logmsg.VNFSPIN_FILE_ERR)
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.VNFSPIN_FILE_ERR)
            return

        self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=c.TASK_STATE_DONE)

    def post_run_task(self):
        pass
