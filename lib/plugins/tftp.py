# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import re
import sys

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogSourcePlg as logmsg
from lib.plugins.sourceplugin import SourcePlugin
from lib.sampledevice import SampleDevice
from lib.tools import Tools


class Tftp(SourcePlugin):
    def __init__(self, plugin_cfg=None):

        super(Tftp, self).__init__(plugin_cfg=plugin_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.TFTP_PLG, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Tftp, SourcePlugin))))
        self.logfile = self.logfile = getattr(c.conf.SERVICES, (plugin_cfg['pluginName']).title()).LogFile
        self.log_pattern = getattr(c.conf.SERVICES, (plugin_cfg['pluginName']).title()).Pattern

    def pre_run_source_plugin(self):
        pass

    def run_source_plugin(self, timestamp):
        """
        :param: timestamp
        :return: sample_device
        """

        try:

            with open(self.logfile) as file:
                log_file_last_line = file.readlines()[-1]

        except IOError:
            self.logger.info(Tools.create_log_msg(logmsg.TFTP_PLG, None, logmsg.TFTP_PLG_FILE_NOK.format(self.logfile)))
            sys.exit()

        if len(log_file_last_line) > 0:

            pattern = r'' + self.log_pattern
            regex = re.compile(pattern, re.MULTILINE)
            deviceIP = list(re.findall(regex, log_file_last_line))

            if deviceIP:
                sample_device = SampleDevice(deviceIP=deviceIP[0], deviceTimeStamp=timestamp,
                                             deviceStatus=c.DEVICE_STATUS_NEW,
                                             deviceSourcePlugin=c.SOURCEPLUGIN_TFTP)
                return sample_device
            else:
                self.logger.info(
                    Tools.create_log_msg(logmsg.TFTP_PLG, None, logmsg.TFTP_PLG_PARSE_NOK.format(log_file_last_line)))
                return None

        else:
            self.logger.info(
                Tools.create_log_msg(logmsg.TFTP_PLG, None, logmsg.TFTP_PLG_PARSE_NOK.format(log_file_last_line)))

    def post_run_source_plugin(self):
        pass
