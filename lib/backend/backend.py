# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

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
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        super(Backend, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
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
                          AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_ADD == body_decoded.message_type:

                response = self.add_device(body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_DEVICE_CFG_ADD == body_decoded.message_type:

                response = self.add_device_config(configSerial=body_decoded.payload['configSerial'],
                                                  configDescr=body_decoded.payload['configDescr'],
                                                  configConfigSource=body_decoded.payload['configConfigSource'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_DEVICE_CFG_DEL == body_decoded.message_type:

                response = self.del_device_config(configSerial=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_DEVICE_GET_CFG_BY_SERIAL == body_decoded.message_type:

                response = self.get_device_config_by_sn(configSerial=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_DEVICE_GET_CFG_ALL == body_decoded.message_type:

                response = self.get_device_configs()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_UPDATE == body_decoded.message_type:

                response = self.update_device(body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_UPDATE_TASK_STATE == body_decoded.message_type:

                device_serial = body_decoded.payload['deviceSerial']
                is_callback = body_decoded.payload['isCallback']
                task_name = body_decoded.payload['taskName']
                task_state = body_decoded.payload['taskState']

                response = self.update_device_task_state(device_serial=device_serial, is_callback=is_callback,
                                                         task_name=task_name,
                                                         task_state=task_state)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_GET_BY_SN == body_decoded.message_type:

                response = self.get_device(body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_GET_BY_CFG_ID == body_decoded.message_type:

                response = self.get_device_by_cfg_id(body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_DEVICE_GET_ALL == body_decoded.message_type:

                response = self.get_devices()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SITE_ADD == body_decoded.message_type:

                response = self.add_site(siteId=body_decoded.payload['siteId'],
                                         siteName=body_decoded.payload['siteName'],
                                         siteDescr=body_decoded.payload['siteDescr'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SITE_DEL == body_decoded.message_type:
                response = self.del_site(siteId=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_ASSET_ADD == body_decoded.message_type:

                response = self.add_asset_to_site(assetSiteId=body_decoded.payload['assetSiteId'],
                                                  assetSerial=body_decoded.payload['assetSerial'],
                                                  assetConfigId=body_decoded.payload['assetConfigId'],
                                                  assetDescr=body_decoded.payload['assetDescr'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_ASSET_GET_BY_SITE == body_decoded.message_type:

                response = self.get_asset_by_site_id(assetSiteId=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_ASSET_GET_BY_SERIAL == body_decoded.message_type:

                response = self.get_asset_by_serial(assetSerial=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_ASSET_UPDATE == body_decoded.message_type:

                response = self.update_asset_site_mapping(assetSerial=body_decoded.payload['assetSerial'],
                                                          assetConfigId=body_decoded.payload['assetConfigId'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SITE_GET_BY_ID == body_decoded.message_type:

                response = self.get_site_by_id(siteId=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SITE_GET_ALL == body_decoded.message_type:

                response = self.get_sites()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_GROUP_ADD == body_decoded.message_type:

                response = self.add_group(groupName=body_decoded.payload['groupName'],
                                          groupConfig=body_decoded.payload['groupConfig'],
                                          groupDescr=body_decoded.payload['groupDescr'],
                                          groupConfigSource=body_decoded.payload['groupConfigSource'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_GROUP_GET_BY_NAME == body_decoded.message_type:

                response = self.get_group_by_name(groupName=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_GROUP_GET_ALL == body_decoded.message_type:

                response = self.get_groups()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_GROUP_DEL == body_decoded.message_type:

                response = self.del_group_by_name(groupName=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_TEMPLATE_ADD == body_decoded.message_type:

                response = self.add_template(templateName=body_decoded.payload['templateName'],
                                             templateConfig=body_decoded.payload['templateConfig'],
                                             templateDescr=body_decoded.payload['templateDescr'],
                                             templateConfigSource=body_decoded.payload['templateConfigSource'],
                                             templateDevGrp=body_decoded.payload['templateDevGrp'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_TEMPLATE_GET_BY_NAME == body_decoded.message_type:

                response = self.get_template_by_name(templateName=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_TEMPLATE_GET_ALL == body_decoded.message_type:

                response = self.get_templates()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_TEMPLATE_DEL == body_decoded.message_type:

                response = self.del_template_by_name(templateName=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_IMAGE_ADD == body_decoded.message_type:

                response = self.add_image(imageName=body_decoded.payload['imageName'],
                                          imageDescr=body_decoded.payload['imageDescr'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_IMAGE_GET_BY_NAME == body_decoded.message_type:

                response = self.get_image_by_name(imageName=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_IMAGE_GET_ALL == body_decoded.message_type:

                response = self.get_images()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_IMAGE_DEL == body_decoded.message_type:

                response = self.del_image_by_name(imageName=body_decoded.payload['imageName'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SVC_GET_BY_NAME == body_decoded.message_type:

                response = self.get_service_by_name(serviceName=body_decoded.payload)
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_SVC_GET_ALL == body_decoded.message_type:

                response = self.get_services()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_SVC_PHS_VALIDATE == body_decoded.message_type:

                response = self.validate_phc(username=body_decoded.payload['username'],
                                             password=body_decoded.payload['password'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_VAL_GET_ALL == body_decoded.message_type:

                response = self.get_validation_all()
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_VAL_VAL_ADD == body_decoded.message_type:

                response = self.add_asset_to_validation_db(username=body_decoded.payload['username'],
                                                           password=body_decoded.payload['password'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_REST_VAL_VAL_DEL == body_decoded.message_type:

                response = self.del_asset_from_validation_db(username=body_decoded.payload['username'])
                self.processRequest(ch=ch, method=method, props=props, response=response)

            else:
                Tools.amqp_receive_error_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

        else:
            self._logger.info('YAPTBACKEND: Recevied empty message')

    def processRequest(self, ch=None, method=None, props=None, response=None):

        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_RESPONSE, payload=response,
                              source=c.AMQP_PROCESSOR_BACKEND)
        encoded = jsonpickle.encode(message)
        ch.basic_publish(exchange='', routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id), body=encoded)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    @abc.abstractmethod
    def add_device(self, new_device):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_device_config(self, configSerial, configDescr, configConfigSource):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_device_config(self, configSerial):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_device_config_by_sn(self, configSerial):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_device_configs(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_device(self, sample_device):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_device_task_state(self, device_serial, is_callback, task_name, task_state):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_device(self, serial_number):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_asset_by_cfg_id(self, cfgId):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_devices(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_site(self, siteId, siteName, siteDescr):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_site(self, siteId):
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
    def get_asset_by_site_id(self, assetSiteId):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_asset_by_serial(self, assetSerial):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_device_by_cfg_id(self, cfgId):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_asset_site_mapping(self, assetSiteId, assetSerial, assetConfigId):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_group(self, groupName, groupConfig, groupDescr, groupConfigSource):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_group_by_name(self, groupName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_group_by_name(self, groupName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_template(self, templateName, templateConfig, templateDescr, templateConfigSource, templateDevGrp):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_template_by_name(self, templateName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_template_by_name(self, templateName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_templates(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_image(self, imageName, imageDescr):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_image_by_name(self, imageName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_image_by_name(self, imageName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_images(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_service_by_name(self, serviceName):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_services(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def validate_phc(self, username, password):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_validation_all(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_asset_to_validation_db(self, username, password):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_asset_from_validation_db(self, username):
        raise NotImplementedError()
