# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import socket

import pynipap
from pynipap import NipapAuthenticationError, NipapValueError
from pynipap import Prefix, AuthOptions

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import Logipam as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class IpamTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(IpamTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(IpamTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        a = AuthOptions({
            'authoritative_source': 'yapt'
        })

        pynipap.xmlrpc_uri = "http://{0}:{1}@{2}:{3}/XMLRPC".format(self.grp_cfg.TASKS.Provision.Ipam.User,
                                                                    self.grp_cfg.TASKS.Provision.Ipam.Password,
                                                                    self.grp_cfg.TASKS.Provision.Ipam.Address,
                                                                    self.grp_cfg.TASKS.Provision.Ipam.Port)

        for prefix in self.grp_cfg.TASKS.Provision.Ipam.Prefixes:

            try:
                p = Prefix.find_free(None, {'from-prefix': [prefix], 'prefix_length': 32})

            except socket.error as se:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.IPAM_CONN_ERR.format(se.strerror))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.IPAM_CONN_ERR.format(se.strerror))

                return
            except NipapAuthenticationError as nae:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.IPAM_CONN_ERR.format(nae.message))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.IPAM_CONN_ERR.format(nae.message))

                return

            if p:
                self.shared[c.TASK_SHARED_IPAM].append(p)
                new_prefix = Prefix()
                new_prefix.prefix = p[0]
                new_prefix.type = 'host'
                new_prefix.description = self.sample_device.deviceSerial
                
                try:
                    new_prefix.save()
                    self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                           task_state_message=c.TASK_STATE_MSG_DONE)
                    Tools.emit_log(task_name=self.task_name,
                                   task_state={'taskState': self.task_state,
                                               'taskStateMsg': c.TASK_STATE_MSG_DONE},
                                   sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                   shared=self.shared,
                                   scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO,
                                   message=logmsg.IPAM_PREFIX_OK.format(prefix))

                except NipapValueError as nve:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.IPAM_PREFIX_ERR.format(nve.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.IPAM_PREFIX_ERR.format(nve.message))

            else:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.IPAM_PREFIX_FULL.format(prefix))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.IPAM_PREFIX_FULL.format(prefix))

    def post_run_task(self):
        pass
