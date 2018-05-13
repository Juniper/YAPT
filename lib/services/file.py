# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import datetime
import os
import threading
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from lib.amqp.amqpmessage import AMQPMessage
from lib.services.service import Service
import lib.constants as c
from lib.tools import Tools
from lib.logmsg import LogCommon
from lib.logmsg import Logfile as logmsg


class File(Service):

    def __init__(self, normalizer, svc_cfg):
        super(File, self).__init__(normalizer=normalizer, svc_cfg=svc_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.FILESVC, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(File, Service))))
        self.logfile = self.svc_cfg['LogFile']
        self.file_svc_t = None

    def start_service(self):

        if self.status == c.SVC_STOPPED or self.status == c.SVC_INIT:
            self.file_svc_t = FileServiceThread(target=self.svc_cfg['svcName'].title(),
                                                name=self.svc_cfg['svcName'],
                                                args=(self.logfile, self.normalizer, self.status))
            self.file_svc_t.observer.start()
            self.status = c.SVC_STARTED
            return self.status
        else:
            return self.status

    def stop_service(self):

        if self.status == c.SVC_STARTED:

            self.file_svc_t.observer.stop()
            self.status = c.SVC_STOPPED
            self.logger.info(
                Tools.create_log_msg(logmsg.FILESVC, None,
                                     logmsg.FILESVC_STOPPED.format(self.logfile)))
            return self.status
        else:
            return self.status

    def restart_service(self):
        if self.status == c.SVC_STOPPED:

            self.start_service()
            return self.status
        else:

            self.stop_service()
            self.start_service()
            return self.status


class FileServiceThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        super(FileServiceThread, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self.file_path = args[0].strip()
        self.log_plugin = args[1]
        self.status = args[2]
        self.watched_dir = os.path.split(self.file_path)[0]
        self.logger = c.logger
        self.patterns = [self.file_path]
        self._stop_service = threading.Event()
        __event_handler = FileHandler(self.log_plugin, patterns=self.patterns)
        self.logger.info(Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_INIT))
        self.logger.info(
            Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_WATCHED_DIR.format(self.watched_dir)))
        self.logger.info(
            Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_PATTERN.format(', '.join(self.patterns))))
        self.observer = Observer()
        self.observer.schedule(__event_handler, self.watched_dir, recursive=True)

    def run(self):

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class FileHandler(PatternMatchingEventHandler):
    def __init__(self, source_plugin=None, patterns=None, ignore_patterns=None, ignore_directories=False,
                 case_sensitive=False):
        super(FileHandler, self).__init__()

        self._source_plugin = source_plugin
        self._patterns = patterns
        self._ignore_patterns = ignore_patterns
        self._ignore_directories = ignore_directories
        self._case_sensitive = case_sensitive
        self.logger = c.logger

    def on_modified(self, event):
        super(FileHandler, self).on_modified(event)
        self.logger.info(Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_MODIFIED.format(event.src_path)))
        payload = self._source_plugin.run_normalizer(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if payload:
            message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD,
                                  payload=self._source_plugin.run_normalizer(
                                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                  source=c.AMQP_PROCESSOR_SVC)
            self._source_plugin.send_message(message=message)
