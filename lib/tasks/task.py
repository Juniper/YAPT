# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc
import os

import yaml
from cerberus import Validator

from lib.amqp.amqpmessage import AMQPMessage
import lib.constants as c
from lib.processor import BackendClientProcessor
from lib.tools import Tools


class Task(object):
    CHECK_SCHEMA = None
    TASK_TYPE = None
    TASK_VERSION = None
    TASK_DESCENT = None

    def __init__(self, sample_device=None, shared=None):

        self.logger = c.logger
        self.task_state = c.TASK_STATE_INIT
        self.task_progress = 0.0
        self.messages = {'error': 'error', 'valid': 'valid', 'invalid': 'invalid', 'deactivated': 'deactivated'}
        self.task_name = self.__class__.__name__.split('Task')[0]
        self.sample_device = sample_device
        self.shared = shared
        self.grp_cfg = Tools.create_config_view(c.CONFIG_TYPE_GROUP, stream=sample_device.deviceGroupData)
        self.task_type = self.__class__.TASK_TYPE
        self.check_schema = self.__class__.CHECK_SCHEMA
        self.task_version = self.__class__.TASK_VERSION
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, 'Validating task configuration'))
        isValid, err = self.__validate_task_config(grp_cfg=sample_device.deviceGroupData)

        if isValid == self.messages['valid']:
            self.logger.info(
                Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, 'Task configuration is valid'))
            self.pre_run_task()
            self.run_task()
            self.post_run_task()

        elif isValid == self.messages['invalid']:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message='Task configuration is invalid. <{0}>'.format(err))
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
            return
        elif isValid == self.messages['error']:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message='Task configuration file not found')
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
            return
        else:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message='Task configuration validation deactivated')
            self.pre_run_task()
            self.run_task()
            self.post_run_task()

    @abc.abstractmethod
    def pre_run_task(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def run_task(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def post_run_task(self):
        raise NotImplementedError()

    def _update_backend(self):

        if self.task_type == c.TASK_TYPE_PROVISION or c.TASK_TYPE_VERIFICATION:

            if 100 % len(self.grp_cfg.TASKS.Sequence) == 0:

                self.sample_device.deviceTaskProgress += self.task_progress

            else:

                if self.task_state == c.TASK_STATE_DONE:

                    if self.sample_device.deviceStatus == c.DEVICE_STATUS_DONE:

                        diff = (100 - (self.task_progress + self.sample_device.deviceTaskProgress))
                        new = self.task_progress + self.sample_device.deviceTaskProgress
                        self.sample_device.deviceTaskProgress = new + diff

                    else:

                        self.sample_device.deviceTaskProgress += self.task_progress

                else:

                    self.sample_device.deviceTaskProgress += self.task_progress

            dev_conn = self.sample_device.deviceConnection
            self.sample_device.deviceConnection = hex(id(self.sample_device.deviceConnection))
            message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_UPDATE, payload=self.sample_device,
                                  source=c.AMQP_PROCESSOR_TASK)
            self._backendp.call(message=message)
            self.sample_device.deviceConnection = dev_conn

    def __validate_task_config(self, grp_cfg=None):

        if getattr(self, 'TASK_DESCENT', None):
            task_name = self.TASK_DESCENT
        else:
            task_name = self.task_name

        if self.check_schema:

            if os.path.exists('conf/schema/task/' + task_name.lower() + '.yml') and os.path.isfile(
                    'conf/schema/task/' + task_name.lower() + '.yml'):

                with open('conf/schema/task/' + task_name.lower() + '.yml', 'r') as stream:
                    schema = yaml.safe_load(stream)
                    v = Validator()
                    v.allow_unknown = True

                if v.validate(document=grp_cfg['TASKS']['Provision'], schema=schema):
                    return self.messages['valid'], None

                else:
                    return self.messages['invalid'], v.errors

            else:
                return self.messages['error'], None

        else:
            return self.messages['deactivated'], None

    def update_task_state(self, new_task_state=c.TASK_STATE_INIT, task_state_message='empty'):

        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message='Current task state <{0}> --> New task state <{1}>'.format(self.task_state,
                                                                                          new_task_state),
                       level=c.LOGGER_LEVEL_DEBUG)

        if getattr(self, 'TASK_DESCENT', None):
            task_name = self.TASK_DESCENT
        else:
            task_name = self.task_name

        if new_task_state == c.TASK_STATE_DONE:

            if task_name == self.grp_cfg.TASKS.Sequence[-1:][0]:

                self.task_state = new_task_state
                self.sample_device.deviceStatus = c.DEVICE_STATUS_DONE
                self.task_progress = self.shared[c.TASK_SHARED_PROGRESS]
                self._update_backend()
                self.sample_device.deviceTasks.taskState[task_name] = {'taskState': new_task_state,
                                                                            'taskStateMsg': task_state_message}
            else:

                self.task_state = new_task_state
                self.sample_device.deviceStatus = c.DEVICE_STATUS_NEXT_TASK
                self.task_progress = self.shared[c.TASK_SHARED_PROGRESS]
                self._update_backend()
                self.sample_device.deviceTasks.taskState[task_name] = {'taskState': new_task_state,
                                                                            'taskStateMsg': task_state_message}

        elif new_task_state == c.TASK_STATE_FAILED:
            self.task_state = new_task_state
            self.sample_device.deviceStatus = c.DEVICE_STATUS_FAILED
            self.sample_device.deviceTasks.taskState[task_name] = {'taskState': new_task_state,
                                                                        'taskStateMsg': task_state_message}

        elif new_task_state == c.TASK_STATE_REBOOT:
            self.task_state = new_task_state
            self.sample_device.deviceStatus = c.DEVICE_STATUS_REBOOTED
            self.sample_device.deviceTasks.taskState[task_name] = {'taskState': new_task_state,
                                                                        'taskStateMsg': task_state_message}

        elif new_task_state == c.TASK_STATE_PROGRESS:
            self.task_state = new_task_state
            self.sample_device.deviceStatus = c.DEVICE_STATUS_PROGRESS
            self._update_backend()
            self.sample_device.deviceTasks.taskState[task_name] = {'taskState': new_task_state,
                                                                        'taskStateMsg': task_state_message}

        else:
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message='Unknown task state <{0}>'.format(self.task_state))
