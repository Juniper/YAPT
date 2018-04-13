# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

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
    def __init__(self, source_plugin, plugin_cfg):
        super(File, self).__init__(source_plugin=source_plugin, plugin_cfg=plugin_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.FILESVC, None, LogCommon.IS_SUBCLASS.format(self.__class__.__name__, issubclass(File, Service))))
        self.logfile = self.logfile = getattr(c.conf.SERVICES, (plugin_cfg['pluginName']).title()).LogFile

    def start_service(self):
        file_service_thread = FileServiceThread(target=self.plugin_cfg['serviceName'].title(),
                                                name=self.plugin_cfg['serviceName'],
                                                args=(self.logfile, self.source_plugin,))
        file_service_thread.start()


class FileServiceThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):

        super(FileServiceThread, self).__init__(group=group, target=target, name=name, verbose=verbose)
        self.file_path = args[0].strip()
        self.log_plugin = args[1]
        self.watched_dir = os.path.split(self.file_path)[0]
        self.logger = c.logger
        self.patterns = [self.file_path]
        __event_handler = FileHandler(self.log_plugin, patterns=self.patterns)
        self.logger.info(Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_INIT))
        self.logger.info(Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_WATCHED_DIR.format(self.watched_dir)))
        self.logger.info(
            Tools.create_log_msg(logmsg.FILESVC, None, logmsg.FILESVC_PATTERN.format(', '.join(self.patterns))))
        self.observer = Observer()
        self.observer.schedule(__event_handler, self.watched_dir, recursive=True)
        self.observer.start()

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
        payload = self._source_plugin.run_source_plugin(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if payload:
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_ADD,
                                  payload=self._source_plugin.run_source_plugin(
                                      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                  source=c.AMQP_PROCESSOR_SVC)
            self._source_plugin.send_message(message=message)
