# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import threading

from lib.amqp.amqpmessage import AMQPMessage
from lib.backend.backend import Backend
import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogInternalBackend as logmsg
from lib.tools import Tools


class Internal(Backend):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):

        super(Internal, self).__init__(group=group, target=target, name=name, args=args, kwargs=None, verbose=None)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(Internal, Backend))))
        self._logger.info(Tools.create_log_msg(logmsg.INTBACKEND, None, logmsg.INTBACKEND_STARTED))
        self.sample_devices = dict()
        self.sample_devices_lock = threading.Lock()

    def add_device(self, new_device):

        if len(self.sample_devices) == 0:

            new_device.deviceStatus = c.DEVICE_STATUS_NEW
            self.sample_devices_lock.acquire()

            try:
                self.sample_devices[new_device.deviceSerial] = dict()
                self.sample_devices[new_device.deviceSerial]['data'] = new_device

            finally:

                self.sample_devices_lock.release()

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_ADD,
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
                        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_UI_UPDATE_AND_RESET,
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

                finally:

                    self.sample_devices_lock.release()

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_ADD,
                                      payload=self.sample_devices[new_device.deviceSerial]['data'],
                                      source=c.AMQP_PROCESSOR_BACKEND)
                self.amqpCl.send_message(message=message)

                return self.sample_devices[new_device.deviceSerial]['data']

    def update_device(self, sample_device):

        self.sample_devices_lock.acquire()

        try:

            self.sample_devices[sample_device.deviceSerial]['data'] = sample_device

        finally:

            self.sample_devices_lock.release()

        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE,
                              payload=self.sample_devices[sample_device.deviceSerial]['data'],
                              source=c.AMQP_PROCESSOR_BACKEND)

        self.amqpCl.send_message(message=message)

        return self.sample_devices[sample_device.deviceSerial]['data']

    def update_device_task_state(self, sample_device, task_name, task_state, task_state_msg):

        self.sample_devices_lock.acquire()

        try:

            try:

                backend_device = self.sample_devices[sample_device.deviceSerial]['data']

                if backend_device.is_callback:
                    backend_device.is_callback = False

                backend_device.deviceTasks.taskState[task_name] = {'taskState': task_state,
                                                                   'taskStateMsg': task_state_msg}
                backend_device.deviceStatus = c.DEVICE_STATUS_TASK_CHANGED

                backend_device.is_callback = True
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE_TASK_STATE,
                                      payload=[self.sample_devices[sample_device.deviceSerial]['data'], task_name],
                                      source=c.AMQP_PROCESSOR_BACKEND)

                self.amqpCl.send_message(message=message)

                return self.sample_devices[sample_device.deviceSerial]['data']

            finally:

                self.sample_devices_lock.release()

        except KeyError as err:
            self._logger.info(Tools.create_log_msg(self.__class__.__name__, sample_device.deviceSerial,
                                                   logmsg.INTBACKEND_KEY_NOK.format(err.message)))

    def get_device(self, serial_number):
        pass

    def get_devices(self):
        return self.sample_devices

    def get_group_by_name(self, groupName):
        pass

    def get_sites(self):
        pass

    def add_site(self, siteId, siteName, siteDescr):
        pass

    def update_asset_site_mapping(self, assetSerial, assetConfigId):
        pass

    def add_group(self, groupName, groupConfig, groupDescr):
        pass

    def add_asset_to_site(self, siteId, assetSerial, assetConfigId, assetDescr):
        pass

    def get_site_by_id(self, siteId):
        pass

    def get_asset_by_serial(self, assetSerial):
        pass

    def get_groups(self):
        pass
