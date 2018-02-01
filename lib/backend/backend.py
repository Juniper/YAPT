# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc

import jsonpickle
import pika
import lib.constants as c

from lib.amqp.amqpadapter import AMQPRpcServerAdapter
from lib.amqp.amqpmessage import AMQPMessage
from lib.logmsg import LogCommon
from lib.processor import ClientProcessor
from lib.tools import Tools


class Backend(AMQPRpcServerAdapter):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):

        super(Backend, self).__init__(group=group, target=target, name=name, args=args, kwargs=None, verbose=None)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(Backend,
                                                                                        AMQPRpcServerAdapter))))
        self.amqpCl = ClientProcessor(exchange=c.conf.AMQP.Exchange, routing_key=c.AMQP_PROCESSOR_UI,
                                      queue=c.AMQP_PROCESSOR_UI)

    def on_request(self, ch, method, props, body):

        if body is not None:

            body_decoded = jsonpickle.decode(body)
            Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

            if isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MESSAGE_TYPE_DEVICE_ADD == body_decoded.message_type:

                response = self.add_device(body_decoded.payload)
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE == body_decoded.message_type:

                response = self.update_device(body_decoded.payload)

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE_TASK_STATE == body_decoded.message_type:

                sample_device = body_decoded.payload['sample_device']
                task_name = body_decoded.payload['taskName']
                task_state = body_decoded.payload['taskState']
                task_state_msg = body_decoded.payload['taskStateMsg']

                response = self.update_device_task_state(sample_device=sample_device, task_name=task_name,
                                                         task_state=task_state, task_state_msg=task_state_msg)
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_SITE_ADD == body_decoded.message_type:

                response = self.add_site(siteId=body_decoded.payload['siteId'],
                                         siteName=body_decoded.payload['siteName'],
                                         siteDescr=body_decoded.payload['siteDescr'])

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_ASSET_ADD == body_decoded.message_type:

                response = self.add_asset_to_site(assetSiteId=body_decoded.payload['assetSiteId'],
                                                  assetSerial=body_decoded.payload['assetSerial'],
                                                  assetConfigId=body_decoded.payload['assetConfigId'],
                                                  assetDescr=body_decoded.payload['assetDescr'])

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_ASSET_GET == body_decoded.message_type:

                response = self.get_asset_by_serial(assetSerial=body_decoded.payload)

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_ASSET_UPDATE == body_decoded.message_type:

                response = self.update_asset_site_mapping(assetSerial=body_decoded.payload['assetSerial'],
                                                          assetConfigId=body_decoded.payload['assetConfigId'])

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_SITE_GET_BY_ID == body_decoded.message_type:

                response = self.get_site_by_id(siteId=body_decoded.payload)

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_SITE_GET_ALL == body_decoded.message_type:

                response = self.get_sites()

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_GROUP_ADD == body_decoded.message_type:

                response = self.add_group(groupName=body_decoded.payload['groupName'],
                                          groupConfig=body_decoded.payload['groupConfig'],
                                          groupDescr=body_decoded.payload['groupDescr'])

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_BY_NAME == body_decoded.message_type:

                response = self.get_group_by_name(groupName=body_decoded.payload)

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_ALL == body_decoded.message_type:

                response = self.get_groups()

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_DEV_GET_BY_SN == body_decoded.message_type:

                response = self.get_device(body_decoded.payload)

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MESSAGE_TYPE_REST_DEV_GET_ALL == body_decoded.message_type:

                response = self.get_devices()

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_RESPONSE, payload=response,
                                      source=c.AMQP_PROCESSOR_BACKEND)
                encoded = jsonpickle.encode(message)

                ch.basic_publish(exchange='', routing_key=props.reply_to,
                                 properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            else:
                Tools.amqp_receive_error_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

        else:
            self._logger.info('YAPTBACKEND: Recevied empty message')

    @abc.abstractmethod
    def add_device(self, new_device):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_device(self, sample_device):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_device_task_state(self, sample_device, task_name, task_state, task_state_msg):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_device(self, serial_number):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_devices(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_site(self, siteId, siteName, siteDescr):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_site_by_id(self, siteId):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_sites(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_asset_to_site(self, assetSiteId, assetSerial, assetConfigId, assetDescr):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_asset_by_serial(self, assetSerial):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_asset_site_mapping(self, assetSerial, assetConfigId):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_group(self, groupName, groupConfig, groupDescr):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_group_by_name(self, groupName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_groups(self):
        raise NotImplementedError()
