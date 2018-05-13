# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import re
import sys

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogSourcePlg as logmsg
from lib.services.normalizer.normalizer import Normalizer
from lib.sampledevice import SampleDevice
from lib.tools import Tools


class Tftp(Normalizer):
    def __init__(self, svc_cfg=None):

        super(Tftp, self).__init__(svc_cfg=svc_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.TFTP_PLG, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Tftp, Normalizer))))
        self.logfile = svc_cfg['LogFile']
        self.pattern = svc_cfg['Module']['Pattern']

    def pre_run_normalizer(self):
        pass

    def run_normalizer(self, timestamp):
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

            pattern = r'' + self.pattern
            regex = re.compile(pattern, re.MULTILINE)
            deviceIP = list(re.findall(regex, log_file_last_line))

            if deviceIP:
                sample_device = SampleDevice(deviceIP=deviceIP[0], deviceTimeStamp=timestamp,
                                             deviceStatus=c.DEVICE_STATUS_INIT,
                                             deviceServicePlugin=c.SERVICEPLUGIN_TFTP)
                return sample_device
            else:
                self.logger.info(
                    Tools.create_log_msg(logmsg.TFTP_PLG, None, logmsg.TFTP_PLG_PARSE_NOK.format(log_file_last_line)))
                return None

        else:
            self.logger.info(
                Tools.create_log_msg(logmsg.TFTP_PLG, None, logmsg.TFTP_PLG_PARSE_NOK.format(log_file_last_line)))

    def post_run_normalizer(self):
        pass
