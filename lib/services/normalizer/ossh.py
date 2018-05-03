# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

from lib.services.normalizer.normalizer import Normalizer
from lib.sampledevice import SampleDevice
from lib.logmsg import LogSourcePlg as logmsg
from lib.logmsg import LogCommon
import lib.constants as c
from lib.tools import Tools


class Ossh(Normalizer):
    def __init__(self, svc_cfg=None):
        """
        :return: raw_devices
        """
        super(Ossh, self).__init__(svc_cfg=svc_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.OSSH_PLG, None,
                                                LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                             issubclass(Ossh, Normalizer))))

    def pre_run_normalizer(self):
        pass

    def run_normalizer(self, timestamp=None, device=None):

        if device:

            sample_device = SampleDevice(deviceIP=device, deviceTimeStamp=timestamp,
                                         deviceStatus=c.DEVICE_STATUS_NEW,
                                         deviceSourcePlugin=c.SOURCEPLUGIN_OSSH)
            sample_device.deviceConnection = device
            return sample_device

        else:
            return "empty"

    def post_run_normalizer(self):
        pass
