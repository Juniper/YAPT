# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

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

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(TailfSvc, self).__init__(group=group, target=target, name=name, verbose=verbose)
        self.logger = c.logger
        self.log_file = args[0]
        self.logger.info(Tools.create_log_msg('LOGVIEWER', None, 'Successfully started Logviewer service'))
        self.logger.info(Tools.create_log_msg('LOGVIEWER', None, 'Observing log file <{0}>'.format(self.log_file)))

    def run(self):
        with open(self.log_file, 'r') as fin:
            self.readlines_then_tail(fin)

    def readlines_then_tail(self, fin):

        while True:
            line = fin.readline()
            if line:
                pass
            else:
                self.tail(fin)

    def tail(self, fin):

        while True:

            where = fin.tell()
            line = fin.readline()
            if not line:
                time.sleep(LogViewer.SLEEP_INTERVAL)
                fin.seek(where)
            else:
                payload = json.dumps(
                    {'data': line.strip(), 'action': c.UI_ACTION_UPDATE_LOG_VIEWER})
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_UI_UPDATE_LOG_VIEWER,
                                      payload=payload, source=c.AMQP_PROCESSOR_SVC)
                clp = ClientProcessor(exchange=c.conf.AMQP.Exchange, routing_key=c.AMQP_PROCESSOR_UI,
                                      queue=c.AMQP_PROCESSOR_UI)
                clp.send_message(message=message)
