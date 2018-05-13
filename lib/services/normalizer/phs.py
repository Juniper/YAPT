# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

from lib.services.normalizer.normalizer import Normalizer
from lib.sampledevice import SampleDevice
from lib.logmsg import LogSourcePlg as logmsg
from lib.logmsg import LogCommon
import lib.constants as c
from lib.tools import Tools


class Phs(Normalizer):
    def __init__(self, svc_cfg=None):
        """
        :return: raw_devices
        """
        super(Phs, self).__init__(svc_cfg=svc_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.PHS_PLG, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Phs, Normalizer))))

    def pre_run_normalizer(self):
        pass

    def run_normalizer(self, timestamp=None, device=None):

        if device is not None:

            sample_device = SampleDevice(deviceIP=device, deviceTimeStamp=timestamp,
                                         deviceStatus=c.DEVICE_STATUS_INIT,
                                         deviceServicePlugin=c.SERVICEPLUGIN_PHS)
            return sample_device

        else:
            return "empty"

    def post_run_normalizer(self):
        pass
