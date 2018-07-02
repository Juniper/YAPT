# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import socket
import jsonpickle
import lib.constants as c

from lib.amqp.amqpadapter import AMQPBlockingServerAdapter
from lib.amqp.amqpmessage import AMQPMessage
from lib.web.logviewer import LogViewer
from lib.logmsg import LogCommon
from lib.logmsg import LogUiProcessor as logmsg
from lib.processor import BackendClientProcessor
from lib.tools import Tools
from lib.web.adapter.amqp2ws import Amqp2ws


class UiProcessor(AMQPBlockingServerAdapter):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        super(UiProcessor, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(UiProcessor,
                                                                                        AMQPBlockingServerAdapter))))
        self.url = 'ws://{0}:{1}/yapt/ws?clientname={2}'.format(c.conf.COMMON.WebUiAddress,
                                                                str(c.conf.COMMON.WebUiPort), c.conf.COMMON.WebUiPlugin)
        self.amqp2ws = Amqp2ws(name=c.conf.COMMON.WebUiPlugin, url=self.url)
        self.backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        LogViewer().run_service()

    def receive_message(self, ch, method, properties, body):

        if body is not None:

            ch.basic_ack(delivery_tag=method.delivery_tag)
            body_decoded = jsonpickle.decode(body)

            if isinstance(body_decoded,
                          AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_ADD == body_decoded.message_type:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)
                message = body_decoded.payload.device_to_json(action=c.UI_ACTION_ADD_DEVICE)
                self.conn_hdlr(message=message)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_UPDATE == body_decoded.message_type:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)
                message = body_decoded.payload.device_to_json(action=c.UI_ACTION_UPDATE_DEVICE)
                self.conn_hdlr(message=message)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_DEVICE_UPDATE_TASK_STATE == body_decoded.message_type:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)

                device_serial = body_decoded.payload[0]
                task_name = body_decoded.payload[1]
                task_state = body_decoded.payload[2]
                message = self.amqp2ws.prepare_device_task_data(device_serial=device_serial,
                                                                action=c.UI_ACTION_UPDATE_TASK_STATE,
                                                                task_name=task_name, task_state=task_state)
                self.conn_hdlr(message=message)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_UI_UPDATE_AND_RESET == body_decoded.message_type:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)
                message = body_decoded.payload.device_to_json(action=c.UI_ACTION_UPDATE_DEVICE_AND_RESET_TASK)
                self.conn_hdlr(message=message)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_UI_UPDATE_AND_REBOOT == body_decoded.message_type:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)
                message = body_decoded.payload.device_to_json(action=c.UI_ACTION_UPDATE_DEVICE)
                self.conn_hdlr(message=message)

            elif isinstance(body_decoded,
                            AMQPMessage) and c.AMQP_MSG_TYPE_UI_UPDATE_LOG_VIEWER == body_decoded.message_type:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)
                self.conn_hdlr(message=body_decoded.payload)

            else:

                Tools.amqp_receive_to_logger(routing_key=method.routing_key, body_decoded=body_decoded)
        else:
            Tools.create_log_msg(self.__class__.__name__, None, logmsg.UIPRO_AMQP_MSG_NOK)

    def send_message(self, message, routing_key):
        pass

    def conn_hdlr(self, message=None):

        amqp2ws = Amqp2ws(name=c.conf.COMMON.WebUiPlugin, url=self.url)

        try:
            amqp2ws.connect()

            if message is not None:
                amqp2ws.send(message)
                amqp2ws.close()
            else:
                Tools.create_log_msg(self.__class__.__name__, None, logmsg.UIPRO_WS_MSG_NOK)

        except socket.error as se:
            Tools.create_log_msg(self.__class__.__name__, None,
                                 logmsg.UIPRO_WS_SOCK_ERR.format(se.message, se.filename, se.strerror, se.args))
