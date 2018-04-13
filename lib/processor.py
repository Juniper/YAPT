# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#


import socket
import uuid

import jnpr.junos
import jsonpickle
import pika
import lib.constants as c

from napalm_base import NetworkDriver
from ncclient.operations.errors import TimeoutExpiredError

from lib.amqp.amqpadapter import AMQPBlockingClientAdapter
from lib.amqp.amqpadapter import AMQPBlockingServerAdapter
from lib.amqp.amqpadapter import AMQPRpcClientAdapter
from lib.amqp.amqpmessage import AMQPMessage
from lib.logmsg import LogCommon
from lib.logmsg import LogTaskProcessor as logmsg
from lib.pluginfactory import SourcePluginFactory
from lib.tools import Tools


class TaskProcessor(AMQPBlockingServerAdapter):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):

        super(TaskProcessor, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs,
                                            verbose=verbose)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(TaskProcessor,
                                                                                        AMQPBlockingServerAdapter))))
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        from lib.tasks.tasktools import Configuration
        self._configurator = Configuration()

    def receive_message(self, ch, method, properties, body):

        if body is not None:

            ch.basic_ack(delivery_tag=method.delivery_tag)
            body_decoded = jsonpickle.decode(body)
            Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

            if isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MESSAGE_TYPE_DEVICE_ADD == body_decoded.message_type:

                sample_device = body_decoded.payload
                status, sample_device = Tools.create_dev_conn(sample_device=sample_device)

                if status:

                    sample_device = Tools.get_device_facts(sample_device=sample_device)
                    status, data = Tools.get_config(lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_GET_DEVICE_CFG,
                                                    sample_device=sample_device)

                    if status:

                        sample_device.deviceConfigData = data

                        try:
                            sample_device.deviceGroup = data['yapt']['device_group']

                        except KeyError as ke:
                            self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                   logmsg.TASKP_STOP_NO_DEVGRP.format(ke.message)))
                            return

                        shared = dict()
                        status, grp_cfg = Tools.get_config(lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_GET_GROUP,
                                                           sample_device=sample_device)

                        if status:

                            sample_device.deviceGroupData = grp_cfg
                            grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)
                            sample_device.deviceTemplate = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile
                            sample_device.deviceTaskSeq = grp_cfg.TASKS.Sequence
                            shared[c.TASK_SHARED_IPAM] = list()
                            shared[c.TASK_SHARED_PROGRESS] = 100 / len(grp_cfg.TASKS.Sequence)
                            # Add task to taskState list in sample_device object before we use it
                            # There should be a better place / way doing this
                            for _task in sample_device.deviceTaskSeq:
                                sample_device.deviceTasks.taskState[_task] = {'taskState': c.TASK_STATE_INIT,
                                                                              'taskStateMsg': c.TASK_STATE_MSG_INIT}

                            dev_conn = sample_device.deviceConnection
                            sample_device.deviceConnection = hex(id(sample_device.deviceConnection))
                            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_ADD, payload=sample_device,
                                                  source=c.AMQP_PROCESSOR_TASK)
                            resp = self._backendp.call(message=message)
                            resp = jsonpickle.decode(resp)
                            sample_device = resp.payload
                            sample_device.deviceConnection = dev_conn
                            tasks_sequence = grp_cfg.TASKS.Sequence
                            # Set deviceSerial as reference in task observer
                            sample_device.deviceTasks.deviceSerial = sample_device.deviceSerial

                            if c.DEVICE_STATUS_NEW == sample_device.deviceStatus \
                                    or c.DEVICE_STATUS_REBOOTED == sample_device.deviceStatus \
                                    or c.DEVICE_STATUS_EXISTS == sample_device.deviceStatus:

                                self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                       logmsg.TASKP_LOAD_TASK_SEQ.format(
                                                                           tasks_sequence)))
                                task_plugins = Tools.load_task_plugins(tasks_sequence)
                                self._logger.debug(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                        logmsg.TASKP_FOUND_TASKPLG.format(
                                                                            len(task_plugins))))
                                if tasks_sequence:

                                    task = None

                                    for _task in tasks_sequence:

                                        from lib.tasks.task import Task

                                        if isinstance(task, Task):

                                            if task.task_state == c.TASK_STATE_DONE:

                                                if _task in task_plugins:

                                                    task = task_plugins[_task]
                                                    self._logger.debug(
                                                        Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                             logmsg.TASKP_FOUND_PLG_ENABLED.format(
                                                                                 _task)))
                                                    task = getattr(task.pop(), _task + 'Task')
                                                    self._logger.debug(
                                                        Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                             logmsg.TASKP_LOADED_PLG_ENABLED.format(
                                                                                 _task)))
                                                    task = task(sample_device, shared)
                                                    self._logger.info(
                                                        Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                             logmsg.TASKP_EXECUTED_PLG_ENABLED.format(
                                                                                 _task)))
                                                else:
                                                    self._logger.info(
                                                        Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                             logmsg.TASKP_NOT_FOUND_PLG_ENABLED.format(
                                                                                 _task)))
                                                    break

                                            elif task.task_state == c.TASK_STATE_REBOOT:
                                                self._logger.info(
                                                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                         logmsg.TASKP_STOP_DEV_REBOOT.format(
                                                                             sample_device.deviceSerial)))

                                            elif task.task_state == c.TASK_STATE_FAILED:
                                                sample_device.deviceStatus = c.DEVICE_STATUS_FAILED
                                                self._logger.info(
                                                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                         logmsg.TASKP_TASK_ERROR.format(
                                                                             _task)))
                                                self.close_dev_conn(sample_device=sample_device)
                                                break

                                            else:
                                                Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                     'Unknown task state <{0}>'.format(task.task_state))

                                        elif task is None:

                                            if _task in task_plugins:

                                                task = task_plugins[_task]
                                                self._logger.debug(
                                                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                         logmsg.TASKP_FOUND_PLG_ENABLED.format(
                                                                             _task)))
                                                task = getattr(task.pop(), _task + 'Task')
                                                self._logger.debug(
                                                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                         logmsg.TASKP_LOADED_PLG_ENABLED.format(
                                                                             _task)))
                                                task = task(sample_device, shared)
                                                self._logger.info(
                                                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                         logmsg.TASKP_EXECUTED_PLG_ENABLED.format(
                                                                             _task)))
                                            else:
                                                self._logger.info(
                                                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                         logmsg.TASKP_NOT_FOUND_PLG_ENABLED.format(
                                                                             _task)))
                                                break

                                        else:
                                            Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                 'Unknown task state <{0}>'.format(task.task_state))

                                else:
                                    self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                           logmsg.TASKP_SEQ_EMPTY))
                                    return
                        else:
                            self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                   logmsg.TASKP_STOP_NO_DEVGRP_CFG.format(grp_cfg)))
                            self.close_dev_conn(sample_device=sample_device)
                            return
                    else:
                        self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                               logmsg.TASKP_STOP_NO_DEV_CFG.format(data)))
                        self.close_dev_conn(sample_device=sample_device)
                        return
                else:
                    self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                           logmsg.TASKP_CONN_ERR.format(sample_device.deviceSerial)))
                    return
            else:
                Tools.amqp_receive_error_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

        else:
            self._logger.info(Tools.create_log_msg(logmsg.TASKP, None, logmsg.TASKP_DEFECT_MSG))

    def send_message(self, message, routing_key):
        if message is not None and isinstance(message, AMQPMessage):

            Tools.amqp_send_to_logger(routing_key=routing_key, body_decoded=message)
            self.send_message_amqp(jsonpickle.encode(message), routing_key=routing_key)

        else:
            Tools.amqp_send_error_to_logger(routing_key=routing_key, body_decoded=message)

    def close_dev_conn(self, sample_device):

        self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                               logmsg.TASKP_CLOSE_DEV_CONN.format(
                                                   hex(id(sample_device.deviceConnection)))))

        if isinstance(sample_device.deviceConnection, NetworkDriver):

            try:
                sample_device.deviceConnection.close()
            except TimeoutExpiredError as texe:
                self._logger.info(
                    Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                         logmsg.TASKP_CONN_ERR_CLOSE.format(
                                             sample_device.deviceIP, texe.message)))
                return

        elif isinstance(sample_device.deviceConnection, jnpr.junos.device.Device):

            if sample_device.deviceSourcePlugin == c.SOURCEPLUGIN_OSSH:
                sample_device.deviceConnection = ''
                message = AMQPMessage(
                    message_type=c.AMQP_MESSAGE_TYPE_SVC_OSSH_CLOSE_SOCKET,
                    payload=sample_device,
                    source=c.AMQP_PROCESSOR_TASK)
                self.send_message(message=message,
                                  routing_key=c.AMQP_PROCESSOR_SERVICE)

            elif sample_device.deviceConnection.connected:
                try:
                    sample_device.deviceConnection.close()
                except TimeoutExpiredError as texe:
                    self._logger.info(
                        Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                             logmsg.TASKP_CONN_ERR_CLOSE.format(
                                                 sample_device.deviceIP, texe.message)))
                    return


class ServiceProcessor(AMQPBlockingServerAdapter):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):

        super(ServiceProcessor, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs,
                                               verbose=verbose)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(ServiceProcessor,
                                                                                        AMQPBlockingServerAdapter))))
        self.registry = SourcePluginFactory(c.conf.YAPT.SourcePlugins).registry

    def receive_message(self, ch, method, properties, body):

        if body is not None:

            ch.basic_ack(delivery_tag=method.delivery_tag)
            body_decoded = jsonpickle.decode(body)
            Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

            if isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MESSAGE_TYPE_SVC_OSSH_CLOSE_SOCKET == body_decoded.message_type:
                sample_device = body_decoded.payload

                if sample_device.deviceIP in c.oss_seen_devices:

                    sock = c.oss_seen_devices[sample_device.deviceIP]['socket']
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                    with c.oss_seen_devices_lck:
                        if sample_device.deviceIP in c.oss_seen_devices:
                            c.oss_seen_devices.pop(sample_device.deviceIP, None)

            elif isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MESSAGE_TYPE_SVC_OSSH_START == body_decoded.message_type:
                print 'starting service'

            elif isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MESSAGE_TYPE_SVC_OSSH_STOP == body_decoded.message_type:
                print 'stopping service'

            elif isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MESSAGE_TYPE_SVC_OSSH_RESART == body_decoded.message_type:
                print 'restarting service'

            else:
                print 'unknow AMQP Message Type'


class BackendClientProcessor(AMQPRpcClientAdapter):
    def __init__(self, exchange=None, routing_key=None):
        AMQPRpcClientAdapter.__init__(self, exchange=exchange, routing_key=routing_key)
        self._logger.debug(Tools.create_log_msg('BACKENDCLPROCESS', None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(BackendClientProcessor,
                                                                                        AMQPRpcClientAdapter))))
        self.__routing_key = routing_key

    def on_response(self, ch, method, props, body):

        if self._corr_id == props.correlation_id:
            self._response = body

    def call(self, message=None):

        Tools.amqp_receive_to_logger(routing_key=self.__routing_key, body_decoded=message)
        self._response = None
        self._corr_id = str(uuid.uuid4())
        self._channel.basic_publish(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE,
                                    properties=pika.BasicProperties(
                                        reply_to=self._callback_queue,
                                        correlation_id=self._corr_id,
                                    ), body=jsonpickle.encode(message))

        while self._response is None:
            self._connection.process_data_events()

        return self._response


class ClientProcessor(AMQPBlockingClientAdapter):
    def __init__(self, exchange=None, routing_key=None, queue=None):

        super(ClientProcessor, self).__init__(exchange=exchange, routing_key=routing_key, queue=queue)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(ClientProcessor,
                                                                                        AMQPBlockingClientAdapter))))

    def send_message(self, message):

        if message is not None:

            if isinstance(message, AMQPMessage):

                Tools.amqp_send_to_logger(routing_key=self._routing_key, body_decoded=message)
                self.send_message_amqp(jsonpickle.encode(message))

            else:

                Tools.amqp_send_error_to_logger(routing_key=self._routing_key, body_decoded=message)
