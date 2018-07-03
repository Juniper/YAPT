# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import collections

import requests
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from requests import ConnectionError

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogTicketTask as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class RtTask(Task):
    CHECK_SCHEMA = True
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0
    TASK_DESCENT = 'Ticket'

    def __init__(self, sample_device=None, shared=None):
        super(RtTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(RtTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        if self.grp_cfg.TASKS.Provision.Ticket.Mode == 'summary':
            self.run_sum_mode()
        elif self.grp_cfg.TASKS.Provision.Ticket.Mode == 'detail':
            self.run_detail_mode()

    def post_run_task(self):
        pass

    def run_sum_mode(self):

        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.TICKET_INIT.format(self.sample_device.deviceSerial,
                                                         self.grp_cfg.TASKS.Provision.Ticket.Rt.Mode))
        url = '{0}://{1}:{2}/login'.format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Protocol,
                                           self.grp_cfg.TASKS.Provision.Ticket.Rt.Address,
                                           self.grp_cfg.TASKS.Provision.Ticket.Rt.Port)

        session = requests.Session()

        data = {
            'username': "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.User),
            'password': "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Password),
            'eauth': "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Eauth),
        }

        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.TICKET_CONN_INIT.format(url))

        resp = None

        try:

            resp = session.post(url, json=data, verify=False)

        except ConnectionError as cer:

            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=cer.message)

        if resp is not None:

            if resp.status_code == 200:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.TICKET_CONN_OK.format(url))

                try:
                    env = Environment(autoescape=False,
                                      loader=FileSystemLoader(self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir),
                                      trim_blocks=True, lstrip_blocks=True)
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message='Found template <{0}>)'.format(
                                               self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Found template directory <{0}>'.format(
                                       self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir))

                except TemplateNotFound as err:

                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message='Error in getting template directory <{0}>'.format(
                                               err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Error in getting template directory <{0}>'.format(err.message))
                    return

                try:
                    template = env.get_template(self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate)
                    tasks = collections.OrderedDict()

                    for task in self.grp_cfg.TASKS.Sequence:
                        tasks[task] = self.sample_device.deviceTasks.taskState[task]

                    ticket_created = template.render(deviceSerial=self.sample_device.deviceSerial,
                                                     deviceName=self.sample_device.deviceName,
                                                     deviceModel=self.sample_device.deviceModel,
                                                     deviceGroup=self.sample_device.deviceGroup,
                                                     deviceStatus=self.sample_device.deviceStatus,
                                                     lastSeen=self.sample_device.deviceTimeStamp, tasks=tasks)

                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message='Successfully rendered template <{0}>'.format(
                                               self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Successfully rendered template <{0}>'.format(
                                       self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate))

                except TemplateNotFound as err:

                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message='Error in getting template file <{0}{1}>'.format(
                                               self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir, err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Error in getting template file <{0}{1}>'.format(
                                       self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir,
                                       err.message))
                    return

                data = {
                    "client": "runner",
                    "fun": "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Functions[0]),
                    "subject": "YAPT new provisioning device <{0}>".format(self.sample_device.deviceSerial),
                    "text": ticket_created,
                    "next_event": "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.NextEvent),
                    "data": dict()
                }

                url = '{0}://{1}:{2}/'.format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Protocol,
                                              self.grp_cfg.TASKS.Provision.Ticket.Rt.Address,
                                              self.grp_cfg.TASKS.Provision.Ticket.Rt.Port)

                resp = None

                try:
                    resp = session.post(url, json=data, verify=False)

                except ConnectionError as cer:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=c.TASK_STATE_MSG_FAILED)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=cer.message)

                if resp is not None:
                    if resp.status_code == 200:

                        data = resp.json()
                        self.shared[c.TASK_SHARED_TICKET] = data['return'][0]['ticket_id']
                        url = '{0}://{1}:{2}/logout'.format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Protocol,
                                                            self.grp_cfg.TASKS.Provision.Ticket.Rt.Address,
                                                            self.grp_cfg.TASKS.Provision.Ticket.Rt.Port)
                        resp = session.post(url, verify=False)

                        if resp.status_code == 200:

                            self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                                   task_state_message=c.TASK_STATE_MSG_DONE)
                            Tools.emit_log(task_name=self.task_name, task_state={
                                self.task_name: self.sample_device.deviceTasks.taskState[self.task_name]},
                                           sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                           shared=self.shared,
                                           message=logmsg.TICKET_CREATE_OK.format(self.shared[c.TASK_SHARED_TICKET]),
                                           scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)

                        else:
                            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                   task_state_message=logmsg.TICKET_CREATE_NOK.format(
                                                       self.shared[c.TASK_SHARED_TICKET],
                                                       resp.status_code))
                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=logmsg.TICKET_CREATE_NOK.format(self.shared[c.TASK_SHARED_TICKET],
                                                                                   resp.status_code))

                    else:
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=logmsg.TICKET_CREATE_NOK.format(
                                                   self.shared[c.TASK_SHARED_TICKET],
                                                   resp.status_code))
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.TICKET_CREATE_NOK.format(self.shared[c.TASK_SHARED_TICKET],
                                                                               resp.status_code))

            else:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.TICKET_CONN_NOK.format(url, resp.status_code))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.TICKET_CONN_NOK.format(url, resp.status_code))

    def run_detail_mode(self):

        # Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
        #               message=logmsg.TICKET_INIT.format(self.sample_device.deviceSerial))
        url = '{0}://{1}:{2}/login'.format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Protocol,
                                           self.grp_cfg.TASKS.Provision.Ticket.Rt.Address,
                                           self.grp_cfg.TASKS.Provision.Ticket.Rt.Port)

        data = {
            'username': "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.User),
            'password': "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Password),
            'eauth': "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Eauth),
        }

        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.TICKET_CONN_INIT.format(url))

        resp = None
        session = requests.Session()

        try:

            resp = session.post(url, json=data, verify=False)

        except ConnectionError as cer:

            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=cer.message)

        if resp is not None:

            if resp.status_code == 200:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.TICKET_CONN_OK.format(url))

                try:
                    env = Environment(autoescape=False,
                                      loader=FileSystemLoader(self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir),
                                      trim_blocks=True, lstrip_blocks=True)
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message='Found template <{0}>)'.format(
                                               self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Found template directory <{0}>'.format(
                                       self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir))

                except TemplateNotFound as err:

                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message='Error in getting template directory <{0}>'.format(
                                               err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Error in getting template directory <{0}>'.format(err.message))
                    return

                try:
                    template = env.get_template(self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate)
                    ticket_created = template.render(deviceSerial=self.sample_device.deviceSerial,
                                                     deviceName=self.sample_device.deviceName,
                                                     deviceModel=self.sample_device.deviceModel,
                                                     deviceGroup=self.sample_device.deviceGroup,
                                                     deviceStatus=self.sample_device.deviceStatus,
                                                     lastSeen=self.sample_device.deviceTimeStamp)
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message='Successfully rendered template <{0}>'.format(
                                               self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Successfully rendered template <{0}>'.format(
                                       self.grp_cfg.TASKS.Provision.Ticket.Rt.TicketCreateTemplate))

                except TemplateNotFound as err:

                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message='Error in getting template file <{0}{1}>'.format(
                                               self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir, err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message='Error in getting template file <{0}{1}>'.format(
                                       self.grp_cfg.TASKS.Provision.Ticket.Rt.TemplateDir,
                                       err.message))
                    return

                data = {
                    "client": "runner",
                    "fun": "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Functions[0]),
                    "subject": "YAPT new provisioning device <{0}>".format(self.sample_device.deviceSerial),
                    "text": ticket_created,
                    "next_event": "{0}".format(self.grp_cfg.TASKS.Provision.Ticket.Rt.NextEvent),
                    "data": dict()
                }

                url = '{0}://{1}:{2}/'.format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Protocol,
                                              self.grp_cfg.TASKS.Provision.Ticket.Rt.Address,
                                              self.grp_cfg.TASKS.Provision.Ticket.Rt.Port)
                try:

                    resp = session.post(url, json=data, verify=False)

                except ConnectionError as cer:

                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=c.TASK_STATE_MSG_FAILED)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device, message=cer.message)

                if resp is not None:

                    if resp.status_code == 200:

                        data = resp.json()
                        self.shared[c.TASK_SHARED_TICKET] = data['return'][0]['ticket_id']
                        url = '{0}://{1}:{2}/logout'.format(self.grp_cfg.TASKS.Provision.Ticket.Rt.Protocol,
                                                            self.grp_cfg.TASKS.Provision.Ticket.Rt.Address,
                                                            self.grp_cfg.TASKS.Provision.Ticket.Rt.Port)
                        resp = session.post(url, verify=False)

                        if resp.status_code == 200:

                            self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                                   task_state_message=c.TASK_STATE_MSG_DONE)
                            Tools.emit_log(task_name=RtTask.TASK_DESCENT,
                                           task_state=self.sample_device.deviceTasks.taskState[RtTask.TASK_DESCENT],
                                           sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                           shared=self.shared,
                                           message=logmsg.TICKET_CREATE_OK.format(self.shared[c.TASK_SHARED_TICKET]),
                                           scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)

                        else:
                            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                   task_state_message=logmsg.TICKET_CREATE_NOK.format(
                                                       self.shared[c.TASK_SHARED_TICKET],
                                                       resp.status_code))
                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=logmsg.TICKET_CREATE_NOK.format(self.shared[c.TASK_SHARED_TICKET],
                                                                                   resp.status_code))

                    else:
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=logmsg.TICKET_CREATE_NOK.format(
                                                   self.shared[c.TASK_SHARED_TICKET],
                                                   resp.status_code))
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.TICKET_CREATE_NOK.format(self.shared[c.TASK_SHARED_TICKET],
                                                                               resp.status_code))

            else:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.TICKET_CONN_NOK.format(url, resp.status_code))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.TICKET_CONN_NOK.format(url, resp.status_code))
