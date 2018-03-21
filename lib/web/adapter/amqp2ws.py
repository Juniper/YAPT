# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import json

from lib.logmsg import LogAmqp as logmsg
import lib.constants as c
from lib.tools import Tools
from lib.web.adapter.adapter import UiAdapter


class Amqp2ws(UiAdapter):
    def __init__(self, name=None, url=None):

        super(Amqp2ws, self).__init__(url=url, protocols=['http-only', 'chat'])
        self.logger = c.logger
        self._clientName = name

    def opened(self):
        self.logger.debug(Tools.create_log_msg(self.__class__.__name__, self._clientName,
                                               logmsg.AMQP_CL_CONN_OK.format(self._clientName)))

    def prepare_device_task_data(self, device_serial=None, action=None, task_name=None, task_state=None):

        data = {"action": action,
                "deviceSerial": device_serial,
                "taskName": task_name,
                "taskState": task_state,
                }

        return json.dumps(data)

    def closed(self, code, reason=None):
        if code != 1000:
            self.logger.debug('AMQP2WS: Connection closed. Code <{0}>, Reason: <{1}>'.format(code, reason))

    def received_message(self, m):
        self.logger.debug('AMQP2WS: Client received data. That\'s not what we want at this stage')
