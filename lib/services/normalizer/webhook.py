# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import lib.constants as c
import jsonpickle
from lib.amqp.amqpmessage import AMQPMessage
from lib.processor import BackendClientProcessor
from lib.services.normalizer.normalizer import Normalizer
from lib.logmsg import LogSourcePlg as logmsg
from lib.logmsg import LogCommon
from lib.tools import Tools


class Webhook(Normalizer):
    def __init__(self, svc_cfg=None):
        """
        :return: raw_devices
        """
        super(Webhook, self).__init__(svc_cfg=svc_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.PHS_PLG, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Webhook, Normalizer))))

    def pre_run_normalizer(self):
        pass

    def run_normalizer(self, timestamp=None, device=None):

        if device:

            message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_GET_BY_SN,
                                  payload=device,
                                  source=c.AMQP_PROCESSOR_SVC)
            backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
            resp = jsonpickle.decode(backendp.call(message=message))

            if resp.payload[0]:
                sample_device = resp.payload[1]
                sample_device.deviceSerial = device
                sample_device.deviceServicePlugin = c.SERVICEPLUGIN_WEBHOOK
                sample_device.deviceTimeStamp = timestamp

                return True, sample_device
            else:
                return False

        else:
            return False

    def post_run_normalizer(self):
        pass
