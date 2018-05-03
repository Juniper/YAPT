# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import yaml
import lib.constants as c
import dependency_injector.containers as containers
import dependency_injector.providers as providers
import jsonpickle

from lib.processor import BackendClientProcessor
from lib.amqp.amqpmessage import AMQPMessage
from lib.logmsg import LogTaskProcessor as logmsg

from lib.tools import Tools


class FactoryContainer(object):

    def __init__(self):

        self.logger = c.logger
        # Creating empty container of service providers
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


class TaskFactory(object):

    # Task factory provider creates new task instance of specified class.
    def __init__(self, sample_device=None, grp_cfg=None):

        self.logger = c.logger
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        self.tasks = list()
        shared = dict()
        sample_device.deviceGroupData = grp_cfg
        grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)
        sample_device.deviceTaskSeq = list(grp_cfg.TASKS.Sequence)
        shared[c.TASK_SHARED_PROGRESS] = 100 / len(sample_device.deviceTaskSeq)
        sample_device.deviceTemplate = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile

        # Set deviceSerial as reference in task observer
        sample_device.deviceTasks.deviceSerial = sample_device.deviceSerial

        dev_conn = sample_device.deviceConnection
        sample_device.deviceConnection = hex(id(sample_device.deviceConnection))
        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD, payload=sample_device,
                              source=c.AMQP_PROCESSOR_TASK)
        resp = self._backendp.call(message=message)
        resp = jsonpickle.decode(resp)
        sample_device = resp.payload
        sample_device.deviceConnection = dev_conn

        if sample_device.deviceTaskSeq:

            for _task in sample_device.deviceTaskSeq:

                task_module = Tools.get_task_module_from_group(grp_cfg=grp_cfg, task_name=_task)
                task = Tools.load_provision_task_plugin(task_name=task_module)
                sample_device.deviceTasks.taskState[_task] = {'taskState': c.TASK_STATE_INIT,
                                                              'taskStateMsg': c.TASK_STATE_MSG_INIT}

                if task:
                    self.tasks.append(providers.Factory(task, sample_device=sample_device, shared=shared))
                else:
                    print 'Error importing task: ' + task_module
                    break

        else:
            self.logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                  logmsg.TASKP_SEQ_EMPTY))
            return

    def get_tasks(self):
        return self.tasks
