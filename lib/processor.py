# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


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
from lib.amqp.amqpadapter import AMQPRpcServerAdapter
from lib.amqp.amqpadapter import AMQPRpcClientAdapter
from lib.amqp.amqpmessage import AMQPMessage
from lib.logmsg import LogCommon
from lib.logmsg import LogTaskProcessor as logmsg
from lib.pluginfactory import ServicePluginFactory
from lib.tools import Tools


class TaskProcessor(AMQPBlockingServerAdapter):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        super(TaskProcessor, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(TaskProcessor,
                                                                                        AMQPBlockingServerAdapter))))
        self._logger.info(Tools.create_log_msg(self.__class__.__name__, None, 'Starting {0}'.format(name)))
        from lib.tasks.tasktools import Configuration
        self._configurator = Configuration()
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        self._svcp = ServiceClientProcessor(exchange='', routing_key=c.AMQP_RPC_SERVICE_QUEUE)

    def receive_message(self, ch, method, properties, body):

        if body is not None:

            ch.basic_ack(delivery_tag=method.delivery_tag)
            body_decoded = jsonpickle.decode(body)
            Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

            if isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_ADD == body_decoded.message_type:

                sample_device = body_decoded.payload
                status, sample_device = Tools.create_dev_conn(sample_device=sample_device)

                if status:

                    sample_device = Tools.get_device_facts(sample_device=sample_device)

                    status, data = Tools.get_config(lookup_type=c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG,
                                                    sample_device=sample_device)

                    if status:

                        sample_device.deviceConfigData = data

                        try:

                            sample_device.deviceGroup = data['yapt']['device_group']

                        except KeyError as ke:
                            self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                   logmsg.TASKP_STOP_NO_DEVGRP.format(ke.message)))
                            return

                        status, grp_cfg = Tools.get_config(lookup_type=c.CONFIG_LOOKUP_TYPE_GET_GROUP,
                                                           sample_device=sample_device)

                        if status:

                            sample_device.deviceGroupData = grp_cfg
                            grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)
                            sample_device.deviceTemplate = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile
                            sample_device.deviceTaskSeq = list(grp_cfg.TASKS.Sequence)
                            dev_conn = sample_device.deviceConnection
                            sample_device.deviceConnection = hex(id(sample_device.deviceConnection))
                            message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD, payload=sample_device,
                                                  source=c.AMQP_PROCESSOR_TASK)
                            resp = self._backendp.call(message=message)
                            resp = jsonpickle.decode(resp)
                            sample_device = resp.payload[1]
                            sample_device.deviceConnection = dev_conn
                            self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                   logmsg.TASKP_LOAD_TASK_SEQ.format(
                                                                       sample_device.deviceTaskSeq)))
                            c.taskq.add_device_task_q(sample_device=sample_device, grp_cfg=grp_cfg)
                            taskq = c.taskq.get_device_task_q(sn=sample_device.deviceSerial)
                            self._logger.debug(Tools.create_log_msg(self.name, sample_device.deviceSerial,
                                                                    'Device status: <{0}>'.format(
                                                                        sample_device.deviceStatus)))
                            if taskq:

                                for task in taskq:
                                    self._logger.debug(Tools.create_log_msg(self.name, sample_device.deviceSerial,
                                                                            'Task: <{0}> status: <{1}>'.format(
                                                                                task.task_name, task.task_state)))

                                    if task.task_state == c.TASK_STATE_INIT:
                                        task.pre_run_task()
                                        task.run_task()
                                        task.post_run_task()

                                        if task.task_state == c.TASK_STATE_REBOOTING:
                                            self._logger.debug(
                                                Tools.create_log_msg(self.name, sample_device.deviceSerial,
                                                                     'Task: <{0}> status: <{1}>'.format(
                                                                         task.task_name, task.task_state)))
                                            self._logger.info(
                                                Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                     logmsg.TASKP_STOP_DEV_REBOOT.format(
                                                                         sample_device.deviceSerial)))
                                            break

                                        elif task.task_state == c.TASK_STATE_FAILED:
                                            self._logger.debug(
                                                Tools.create_log_msg(self.name, sample_device.deviceSerial,
                                                                     'Task: <{0}> status: <{1}>'.format(
                                                                         task.task_name, task.task_state)))
                                            self._logger.info(
                                                Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                     logmsg.TASKP_TASK_ERROR.format(
                                                                         task.task_name, )))
                                            self.close_dev_conn(sample_device=sample_device)
                                            break

                                    elif task.task_state == c.TASK_STATE_REBOOTING:
                                        task.pre_run_task()
                                        task.run_task()
                                        task.post_run_task()

                                        if task.task_state == c.TASK_STATE_FAILED:
                                            self._logger.debug(
                                                Tools.create_log_msg(self.name, sample_device.deviceSerial,
                                                                     'Task: <{0}> status: <{1}>'.format(
                                                                         task.task_name, task.task_state)))
                                            self._logger.info(
                                                Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                     logmsg.TASKP_TASK_ERROR.format(
                                                                         task.task_name, )))
                                            self.close_dev_conn(sample_device=sample_device)
                                            break

                                    elif task.task_state == c.TASK_STATE_DONE:
                                        pass

                                    elif task.task_state == c.TASK_STATE_FAILED:
                                        self._logger.debug(
                                            Tools.create_log_msg(self.name, sample_device.deviceSerial,
                                                                 'Task: <{0}> status: <{1}>'.format(
                                                                     task.task_name, task.task_state)))
                                        self._logger.info(
                                            Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                 logmsg.TASKP_TASK_ERROR.format(
                                                                     task.task_name, )))
                                        self.close_dev_conn(sample_device=sample_device)
                                        break

                                    else:
                                        self._logger.info(Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                                                               'Task <{0}> state: <{1}> unknown'.format(
                                                                                   task.task_name, task.task_state)))
                                        break

                                # print 'After running all tasks device status is: <{0}>'.format(
                                #    sample_device.deviceStatus)

                                if sample_device.deviceStatus == c.DEVICE_STATUS_DONE:
                                    c.taskq.del_device_task_q(sample_device.deviceSerial)
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

            if sample_device.deviceServicePlugin == c.SERVICEPLUGIN_OSSH:
                sample_device.deviceConnection = ''
                message = AMQPMessage(
                    message_type=c.AMQP_MSG_TYPE_SVC_OSSH_CLOSE_SOCKET,
                    payload=sample_device,
                    source=c.AMQP_PROCESSOR_TASK)

                response = self._svcp.call(message=message)
                response = jsonpickle.decode(response)

            elif sample_device.deviceConnection.connected:
                try:
                    sample_device.deviceConnection.close()
                except TimeoutExpiredError as texe:
                    self._logger.info(
                        Tools.create_log_msg(logmsg.TASKP, sample_device.deviceSerial,
                                             logmsg.TASKP_CONN_ERR_CLOSE.format(
                                                 sample_device.deviceIP, texe.message)))
                    return


class ServiceProcessor(AMQPRpcServerAdapter):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        super(ServiceProcessor, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(ServiceProcessor,
                                                                                        AMQPBlockingServerAdapter))))
        self._logger.info(Tools.create_log_msg(self.__class__.__name__, None, 'Starting {0}'.format(name)))
        self.registry = ServicePluginFactory(c.conf.SERVICES.Plugins).registry

    def on_request(self, ch, method, props, body):

        if body is not None:

            body_decoded = jsonpickle.decode(body)
            Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

            if isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MSG_TYPE_SVC_OSSH_CLOSE_SOCKET == body_decoded.message_type:
                sample_device = body_decoded.payload

                if sample_device.deviceIP in c.oss_seen_devices:
                    # Todo: Move to service OSSH

                    sock = c.oss_seen_devices[sample_device.deviceIP]['socket']
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

                    with c.oss_seen_devices_lck:
                        if sample_device.deviceIP in c.oss_seen_devices:
                            c.oss_seen_devices.pop(sample_device.deviceIP, None)
                self.process_req(ch=ch, method=method, props=props, response=c.AMQP_MSG_TYPE_RESPONSE)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SVC_START == body_decoded.message_type:
                resp = self.registry[body_decoded.payload].start_service()
                self.process_req(ch=ch, method=method, props=props, response=resp)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SVC_STOP == body_decoded.message_type:
                resp = self.registry[body_decoded.payload].stop_service()
                self.process_req(ch=ch, method=method, props=props, response=resp)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SVC_RESTART == body_decoded.message_type:
                resp = self.registry[body_decoded.payload].restart_service()
                self.process_req(ch=ch, method=method, props=props, response=resp)

            else:
                self._logger.info(Tools.create_log_msg('SVCPROCESSOR', None, 'Unknown AMQP message type'))

    @staticmethod
    def process_req(ch=None, method=None, props=None, response=None):

        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_RESPONSE, payload=response,
                              source=c.AMQP_PROCESSOR_SVC)
        encoded = jsonpickle.encode(message)
        ch.basic_publish(exchange='', routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
        ch.basic_ack(delivery_tag=method.delivery_tag)


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


class ServiceClientProcessor(AMQPRpcClientAdapter):
    def __init__(self, exchange=None, routing_key=None):
        AMQPRpcClientAdapter.__init__(self, exchange=exchange, routing_key=routing_key)
        self._logger.debug(Tools.create_log_msg('SVCCLPROCESSOR', None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(ServiceClientProcessor,
                                                                                        AMQPRpcClientAdapter))))
        self.__routing_key = routing_key

    def on_response(self, ch, method, props, body):

        if self._corr_id == props.correlation_id:
            self._response = body

    def call(self, message=None):

        Tools.amqp_receive_to_logger(routing_key=self.__routing_key, body_decoded=message)
        self._response = None
        self._corr_id = str(uuid.uuid4())
        self._channel.basic_publish(exchange='', routing_key=c.AMQP_RPC_SERVICE_QUEUE,
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
