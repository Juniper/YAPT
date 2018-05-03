# Copyright (c) 2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar
#

import os
import json
import threading
import time
from lib.tools import Tools
from lib.amqp.amqpmessage import AMQPMessage
import lib.constants as c
from lib.processor import ClientProcessor


class LogViewer():
    SLEEP_INTERVAL = 1.0

    def __init__(self):
        self.logger = c.logger
        self.logfile = c.conf.EMITTER.MainLogFile

    def run_service(self):
        tailfsvc = TailfSvc(target=TailfSvc, name='TailfSvc', args=(self.logfile,))
        tailfsvc.start()


class TailfSvc(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, ):
        super(TailfSvc, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.logger = c.logger
        self.log_file = args[0]
        self.logger.info(Tools.create_log_msg('LOGVIEWER', None, 'Successfully started Logviewer service'))
        self.logger.info(Tools.create_log_msg('LOGVIEWER', None, 'Observing log file <{0}>'.format(self.log_file)))
        self.clp = ClientProcessor(exchange=c.conf.AMQP.Exchange, routing_key=c.AMQP_PROCESSOR_UI,
                                   queue=c.AMQP_PROCESSOR_UI)

    def run(self):
        fd = open('./logs/info.log', 'r+')

        for line in self.tail(fd):
            payload = json.dumps({'data': line.strip(), 'action': c.UI_ACTION_UPDATE_LOG_VIEWER})
            message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_UI_UPDATE_LOG_VIEWER,
                                  payload=payload, source=c.AMQP_PROCESSOR_SVC)
            self.clp.send_message(message=message)

    def tail(self, theFile):
        theFile.seek(0, 2)  # Go to the end of the file
        while True:
            line = theFile.readline()
            if not line:
                time.sleep(LogViewer.SLEEP_INTERVAL)
                continue
            yield line
