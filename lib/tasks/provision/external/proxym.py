# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


import requests
import lib.constants as c

from requests import ConnectionError
from lib.logmsg import LogCommon
from lib.tasks.task import Task
from lib.tools import Tools


class ProxymTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0
    TASK_DESCENT = None

    def __init__(self, sample_device=None, shared=None):
        super(ProxymTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(ProxymTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        url = '{0}://{1}:{2}/login'.format(self.grp_cfg.TASKS.Provision.Proxym.Protocol,
                                           self.grp_cfg.TASKS.Provision.Proxym.Address,
                                           self.grp_cfg.TASKS.Provision.Proxym.Port)

        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, url))

        session = requests.Session()

        data = {
            'username': "{0}".format(self.grp_cfg.TASKS.Provision.Proxym.User),
            'password': "{0}".format(self.grp_cfg.TASKS.Provision.Proxym.Password),
            'eauth': "{0}".format(self.grp_cfg.TASKS.Provision.Proxym.Eauth),
        }

        resp = None

        try:
            resp = session.post(url, json=data, verify=False)
            self.logger.info(
                Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, resp.status_code))

        except ConnectionError as cer:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=cer.message)

        url = '{0}://{1}:{2}/{3}'.format(self.grp_cfg.TASKS.Provision.Proxym.Protocol,
                                         self.grp_cfg.TASKS.Provision.Proxym.Address,
                                         self.grp_cfg.TASKS.Provision.Proxym.Port,
                                         self.grp_cfg.TASKS.Provision.Proxym.Tag)

        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, url))

        data = {
            'device_ip': self.sample_device.deviceIP, 'hostname': self.sample_device.deviceName,
            'username': c.conf.COMMON.DeviceUsr,
            'password': 'juniper123', 'dev_sn': self.sample_device.deviceSerial,
            'ticket_id': self.shared[c.TASK_SHARED_TICKET]
        }

        resp = session.post(url, json=data, verify=False)
        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, resp.status_code))

        url = '{0}://{1}:{2}/logout'.format(self.grp_cfg.TASKS.Provision.Proxym.Protocol,
                                            self.grp_cfg.TASKS.Provision.Proxym.Address,
                                            self.grp_cfg.TASKS.Provision.Proxym.Port)

        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, url))
        resp = session.post(url, verify=False)
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, resp.status_code))

    def post_run_task(self):
        pass
