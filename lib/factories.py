# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import threading
import yaml
import lib.constants as c
import dependency_injector.containers as containers
# import dependency_injector.providers as providers

from lib.logmsg import LogTaskProcessor as logmsg

from lib.tools import Tools


class FactoryContainer(object):

    def __init__(self):

        self.logger = c.logger
        # Creating empty container of providers
        self.__fc = containers.DynamicContainer()

        # Load factories configuration

        with open('conf/yapt/factories.yml', 'r') as fd:
            fact_cfg = yaml.safe_load(fd)

        for fact_name, fact_info in fact_cfg['factories'].iteritems():

            factory_cls = Tools.load_factory(fact_info['class'])
            factory_provider_cls = Tools.load_factory(fact_info['provider_class'])

            if factory_cls and factory_provider_cls:
                setattr(self.__fc, fact_name, factory_provider_cls(factory_cls))

    def get_factory_container(self):
        return self.__fc


class TaskQ(object):

    def __init__(self):

        self.logger = c.logger
        self.__taskq = dict()
        self.__taskq_lock = threading.Lock()

    def add_device_task_q(self, sample_device=None, grp_cfg=None):

        shared = dict()
        shared[c.TASK_SHARED_PROGRESS] = 100 / len(sample_device.deviceTaskSeq)

        if sample_device.deviceStatus == c.DEVICE_STATUS_NEW:

            if sample_device.deviceTaskSeq:
                tasks = list()

                for _task in sample_device.deviceTaskSeq:

                    task_module = Tools.get_task_module_from_group(grp_cfg=grp_cfg, task_name=_task)
                    task = Tools.load_provision_task_plugin(task_name=task_module)
                    task = task(sample_device=sample_device, shared=shared)

                    if task:
                        tasks.append(task)
                    else:
                        self.logger.info(Tools.create_log_msg('TASKQ', sample_device.deviceSerial,
                                                              'Error importing task <{0}>'.format(task_module)))
                        break

                self.__taskq_lock.acquire()

                try:
                    self.__taskq[sample_device.deviceSerial] = tasks
                finally:
                    self.__taskq_lock.release()

            else:
                self.logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                      logmsg.TASKP_SEQ_EMPTY))
                return

        elif sample_device.deviceStatus == c.DEVICE_STATUS_EXISTS:

            if sample_device.deviceTaskSeq:
                tasks = list()

                for _task in sample_device.deviceTaskSeq:

                    task_module = Tools.get_task_module_from_group(grp_cfg=grp_cfg, task_name=_task)
                    task = Tools.load_provision_task_plugin(task_name=task_module)
                    task = task(sample_device=sample_device, shared=shared)
                    # task.task_state = sample_device.deviceTasks.taskState[_task]

                    if task:
                        # tasks.append(providers.Factory(task(sample_device=sample_device, shared=shared)))
                        tasks.append(task)
                    else:
                        self.logger.info(Tools.create_log_msg('TASKQ', sample_device.deviceSerial,
                                                              'Error importing task <{0}>'.format(task_module)))
                        break

                self.__taskq[sample_device.deviceSerial] = tasks

            else:
                self.logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                      logmsg.TASKP_SEQ_EMPTY))
                return

        elif sample_device.deviceStatus == c.DEVICE_STATUS_REBOOTED:

            if sample_device.deviceTaskSeq:
                taskq = self.get_device_task_q(sample_device.deviceSerial)

                for task in taskq:
                    self.logger.debug(Tools.create_log_msg('TASKQ', sample_device.deviceSerial,
                                                           'Task <{0}> status <{1}>'.format(task.task_name,
                                                                                            task.task_state)))
                    task.sample_device = sample_device

            else:
                self.logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                      logmsg.TASKP_SEQ_EMPTY))
                return

    def get_device_task_q(self, sn=None):

        if sn in self.__taskq:
            return self.__taskq[sn]
        else:
            return False

    def del_device_task_q(self, sn=None):

        if sn in self.__taskq:

            self.__taskq_lock.acquire()

            try:
                del self.__taskq[sn]
                return True
            finally:
                self.__taskq_lock.release()

        else:
            return False
