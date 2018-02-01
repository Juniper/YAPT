# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import requests
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from requests.exceptions import ConnectionError

import lib.constants as c
from lib.emitter.emitter import Emitter
from lib.tools import Tools


class Ticket(Emitter):

    def __init__(self):
        super(Ticket, self).__init__()

    def emit(self, task_name=None, task_state=None, sample_device=None, grp_cfg=None, shared=None, message=None,
             level=c.LOGGER_LEVEL_INFO):

        if 'Ticket' in grp_cfg.TASKS.Sequence:

            if c.TASK_SHARED_TICKET in shared:

                url = 'https://{0}:{1}/login'.format(grp_cfg.TASKS.Provision.Ticket.Address,
                                                     grp_cfg.TASKS.Provision.Ticket.Port)
                session = requests.Session()

                data = {
                    'username': "{0}".format(grp_cfg.TASKS.Provision.Ticket.User),
                    'password': "{0}".format(grp_cfg.TASKS.Provision.Ticket.Password),
                    'eauth': "{0}".format(grp_cfg.TASKS.Provision.Ticket.Eauth),
                }

                resp = None

                try:
                    resp = session.post(url, json=data, verify=False)

                except ConnectionError as cer:
                    Tools.emit_log(task_name=task_name, sample_device=sample_device, message=cer.message)

                if resp is not None:

                    if resp.status_code == 200:

                        url = 'https://{0}:{1}/'.format(grp_cfg.TASKS.Provision.Ticket.Address,
                                                        grp_cfg.TASKS.Provision.Ticket.Port)

                        try:
                            env = Environment(autoescape=False,
                                              loader=FileSystemLoader(grp_cfg.TASKS.Provision.Ticket.TemplateDir),
                                              trim_blocks=True, lstrip_blocks=True)

                            self.logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                                  'Found template directory <{0}>)'.format(
                                                                      grp_cfg.TASKS.Provision.Ticket.TemplateDir)))
                        except TemplateNotFound as err:

                            self.logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                                  'Error in getting template directory <{0}>'.format(
                                                                      err.message)))
                            return

                        try:
                            template = env.get_template(grp_cfg.TASKS.Provision.Ticket.TicketUpdateTemplate)
                            ticket_updated = template.render(deviceSerial=sample_device.deviceSerial,
                                                             deviceName=sample_device.deviceName,
                                                             deviceModel=sample_device.deviceModel,
                                                             deviceGroup=sample_device.deviceGroup,
                                                             deviceStatus=sample_device.deviceStatus,
                                                             lastSeen=sample_device.deviceTimeStamp,
                                                             taskName=task_name, tasks=task_state)

                        except TemplateNotFound as err:
                            self.logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                                  'Error in getting template file <{0}{1}>'.format(
                                                                      grp_cfg.TASKS.Provision.Ticket.TemplateDir,
                                                                      err.message)
                                                                  ))
                            return

                        data = {
                            "client": "runner",
                            "fun": "{0}".format(grp_cfg.TASKS.Provision.Ticket.Functions[1]),
                            "ticket_id": shared[c.TASK_SHARED_TICKET],
                            "text": "{0}".format(ticket_updated),
                            "status": ""
                        }

                        resp = session.post(url, json=data, verify=False)

                        if resp.status_code == 200:
                            url = 'https://{0}:{1}/logout'.format(grp_cfg.TASKS.Provision.Ticket.Address,
                                                                  grp_cfg.TASKS.Provision.Ticket.Port)
                            resp = session.post(url, verify=False)

                            if resp.status_code == 200:
                                self.logger.info(
                                    Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                         'Successfully updated ticket with ID <{0}>'.format(
                                                             shared[c.TASK_SHARED_TICKET])))

                        else:
                            self.logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                                  'Failure in updating ticket <{0}> with error <{1}>'.format(
                                                                      shared[c.TASK_SHARED_TICKET], resp.status_code)))

                    else:
                        self.logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                              'Failure in updating ticket <{0}>'.format(
                                                                  shared[c.TASK_SHARED_TICKET])))
            else:
                self.logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                      'Not updating ticket since no ticket id yet'))
        else:
            self.logger.debug(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                   'Not processing ticket update since not in task sequence'))
