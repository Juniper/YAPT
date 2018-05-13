# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import threading

from lib.amqp.amqpmessage import AMQPMessage
from lib.backend.backend import Backend
import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogInternalBackend as logmsg
from lib.tools import Tools


class Internal(Backend):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        super(Internal, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(Internal, Backend))))
        self._logger.info(Tools.create_log_msg(logmsg.INTBACKEND, None, logmsg.INTBACKEND_STARTED))
        self.sample_devices = dict()
        self.sample_devices_lock = threading.Lock()
        self.sites = dict()
        self.sites_lock = threading.Lock()
        self.groups = dict()
        self.groups_lock = threading.Lock()

    def add_device(self, new_device=None):

        if len(self.sample_devices) == 0:

            new_device.deviceStatus = c.DEVICE_STATUS_NEW
            self.sample_devices_lock.acquire()

            try:
                self.sample_devices[new_device.deviceSerial] = dict()
                self.sample_devices[new_device.deviceSerial]['data'] = new_device

                if c.DEVICE_STATUS_NEW == self.sample_devices[new_device.deviceSerial]['data'].deviceStatus:

                    self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.is_callback = False

                    for task in self.sample_devices[new_device.deviceSerial]['data'].deviceTaskSeq:
                        self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.taskState[task] = {
                            'taskState': c.TASK_STATE_WAIT,
                            'taskStateMsg': c.TASK_STATE_MSG_WAIT}

                self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.is_callback = True

            finally:

                self.sample_devices_lock.release()

            message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD,
                                  payload=self.sample_devices[new_device.deviceSerial]['data'],
                                  source=c.AMQP_PROCESSOR_BACKEND)
            self.amqpCl.send_message(message=message)

            return self.sample_devices[new_device.deviceSerial]['data']

        elif len(self.sample_devices) > 0:

            if new_device.deviceSerial in self.sample_devices:

                self.sample_devices_lock.acquire()

                try:

                    backend_device = self.sample_devices[new_device.deviceSerial]['data']

                    if new_device.deviceTimeStamp > backend_device.deviceTimeStamp:

                        backend_device = new_device
                        backend_device.deviceStatus = c.DEVICE_STATUS_EXISTS
                        self.sample_devices[new_device.deviceSerial]['data'] = backend_device
                        self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.is_callback = False

                        for task in self.sample_devices[new_device.deviceSerial]['data'].deviceTaskSeq:
                            self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.taskState[task] = {
                                'taskState': c.TASK_STATE_WAIT,
                                'taskStateMsg': c.TASK_STATE_MSG_WAIT}

                        self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.is_callback = True

                        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_UI_UPDATE_AND_RESET,
                                              payload=backend_device, source=c.AMQP_PROCESSOR_BACKEND)
                        self.amqpCl.send_message(message=message)

                        return self.sample_devices[backend_device.deviceSerial]['data']

                    else:
                        self._logger.info(Tools.create_log_msg(logmsg.INTBACKEND, new_device.deviceSerial,
                                                               logmsg.INTBAKCEND_TIMESTAMP_NOK))

                finally:

                    self.sample_devices_lock.release()

            else:

                new_device.deviceStatus = c.DEVICE_STATUS_NEW

                self.sample_devices_lock.acquire()

                try:
                    self.sample_devices[new_device.deviceSerial] = dict()
                    self.sample_devices[new_device.deviceSerial]['data'] = new_device
                    self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.is_callback = False

                    for task in self.sample_devices[new_device.deviceSerial]['data'].deviceTaskSeq:
                        self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.taskState[task] = {
                            'taskState': c.TASK_STATE_WAIT,
                            'taskStateMsg': c.TASK_STATE_MSG_WAIT}

                    self.sample_devices[new_device.deviceSerial]['data'].deviceTasks.is_callback = True

                finally:

                    self.sample_devices_lock.release()

                message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD,
                                      payload=self.sample_devices[new_device.deviceSerial]['data'],
                                      source=c.AMQP_PROCESSOR_BACKEND)
                self.amqpCl.send_message(message=message)

                return self.sample_devices[new_device.deviceSerial]['data']

    def update_device(self, sample_device=None):

        self.sample_devices_lock.acquire()

        try:

            self.sample_devices[sample_device.deviceSerial]['data'] = sample_device

        finally:

            self.sample_devices_lock.release()

        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_UPDATE,
                              payload=self.sample_devices[sample_device.deviceSerial]['data'],
                              source=c.AMQP_PROCESSOR_BACKEND)

        self.amqpCl.send_message(message=message)

        return self.sample_devices[sample_device.deviceSerial]['data']

    def update_device_task_state(self, device_serial=None, is_callback=None, task_name=None, task_state=None):

        self.sample_devices_lock.acquire()

        try:

            try:

                backend_device = self.sample_devices[device_serial]['data']
                backend_device.deviceTasks.is_callback = False
                backend_device.deviceTasks.taskState[task_name] = {'taskState': task_state['taskState'],
                                                                   'taskStateMsg': task_state['taskStateMsg']}
                backend_device.deviceTasks.is_callback = True
                message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_UPDATE_TASK_STATE,
                                      payload=[device_serial, task_name, task_state],
                                      source=c.AMQP_PROCESSOR_BACKEND)

                self.amqpCl.send_message(message=message)

                return self.sample_devices[device_serial]['data']

            finally:

                self.sample_devices_lock.release()

        except KeyError as err:
            self._logger.info(Tools.create_log_msg(self.__class__.__name__, device_serial,
                                                   logmsg.INTBACKEND_KEY_NOK.format(err.message)))

    def get_device(self, serial_number=None):
        return self.sample_devices[serial_number]['data']

    def get_devices(self):
        return self.sample_devices

    def get_group_by_name(self, groupName):
        pass

    def get_sites(self):
        return self.sites

    def add_site(self, siteId=None, siteName=None, siteDescr=None):

        self.sites_lock.acquire()

        try:
            if siteId not in self.sites:
                self.sites[siteId] = {'siteId': siteId, 'siteName': siteName, 'siteDescr': siteDescr, 'assets': dict()}
                return True, 'Successfully added site with ID <{0}> to database'.format(siteId)
            else:
                return False, 'Site with ID <{0}> already exists in database'.format(siteId)

        finally:

            self.sites_lock.release()

    def update_asset_site_mapping(self, assetSiteId=None, assetSerial=None, assetConfigId=None):

        self.sites_lock.acquire()

        try:

            if assetConfigId in self.sites[assetSiteId]['assets']:
                self.sites[assetSiteId]['assets'][assetConfigId] = {'assetSerial': assetSerial,
                                                                    'assetConfigId': assetConfigId}
                return True, 'Successfully mapped asset serial <{0}> to asset config id <{1}>'.format(assetSerial,
                                                                                                      assetConfigId)
            else:
                return False, 'Failed to map asset serial <{0}> to config id <{1}>. Config id does not exists'.format(
                    assetSerial, assetConfigId)

        finally:

            self.sites_lock.release()

    def add_group(self, groupName=None, groupConfig=None, groupDescr=None, groupConfigSource=None):

        self.groups_lock.acquire()

        try:

            if groupName not in self.groups:
                self.groups[groupName] = {'groupName': groupName, 'groupConfig': groupConfig, 'groupDescr': groupDescr}
                return True, 'Successfully added group <{0}> to database'.format(groupName)
            else:
                return False, 'Group with name <{0}> already exists in database'.format(groupName)

        finally:

            self.groups_lock.release()

    def add_asset_to_site(self, assetSiteId=None, assetSerial=None, assetConfigId=None, assetDescr=None):

        self.sites_lock.acquire()

        try:

            if assetSiteId in self.sites:
                if assetConfigId not in self.sites[assetSiteId]['assets']:
                    self.sites[assetSiteId]['assets'][assetConfigId] = {'assetSerial': assetSerial,
                                                                        'assetConfigId': assetConfigId,
                                                                        'assetDescr': assetDescr}
                    return True, 'Successfully added asset with ID <{0}> to site with ID <{1}>'.format(assetConfigId,
                                                                                                       assetSiteId)
                else:
                    return False, 'Asset with serial <{0}> already exists in databse'.format(assetConfigId)
            else:
                return False, 'Site with ID <{0}> does not exists in database'.format(assetSiteId)

        finally:

            self.sites_lock.release()

    def get_site_by_id(self, siteId=None):

        if siteId in self.sites:
            return True, self.sites[siteId]
        else:
            return False, 'Site with id <{0}> not found in database'.format(siteId)

    def get_asset_by_serial(self, assetSerial=None):
        return

    def get_groups(self):
        return self.groups

    def add_device_config(self, configSerial, configDescr, configConfigSource):
        pass

    def del_device_config(self, configSerial):
        pass

    def get_device_config_by_sn(self, configSerial):
        pass

    def get_device_configs(self):
        pass

    def del_site(self, siteId):
        pass

    def get_asset_by_site_id(self, assetSiteId):
        pass

    def del_group_by_name(self, groupName):
        pass

    def add_template(self, templateName, templateConfig, templateDescr, templateConfigSource, templateDevGrp):
        pass

    def del_template_by_name(self, templateName):
        pass

    def get_template_by_name(self, templateName):
        pass

    def get_templates(self):
        pass

    def add_image(self, imageName, imageDescr):
        pass

    def del_image_by_name(self, imageName):
        pass

    def get_image_by_name(self, imageName):
        pass

    def get_images(self):
        pass

    def get_service_by_name(self, serviceName):
        pass

    def get_services(self):
        pass

    def validate_phc(self, username, password):
        pass

    def get_validation_all(self):
        pass

    def add_asset_to_validation_db(self, username, password):
        pass

    def del_asset_from_validation_db(self, username):
        pass
