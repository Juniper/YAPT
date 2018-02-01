# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

from lib.plugins.sourceplugin import SourcePlugin
from lib.sampledevice import SampleDevice
from lib.logmsg import LogSourcePlg as logmsg
from lib.logmsg import LogCommon
import lib.constants as c
from lib.tools import Tools


class Phs(SourcePlugin):
    def __init__(self, plugin_cfg=None):
        """
        :return: raw_devices
        """
        super(Phs, self).__init__(plugin_cfg=plugin_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.PHS_PLG, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Phs, SourcePlugin))))

    def pre_run_source_plugin(self):
        pass

    def run_source_plugin(self, timestamp=None, device=None):

        if device is not None:

            sample_device = SampleDevice(deviceIP=device, deviceTimeStamp=timestamp,
                                         deviceStatus=c.DEVICE_STATUS_NEW,
                                         deviceSourcePlugin=c.SOURCEPLUGIN_PHS)
            return sample_device

        else:
            return "empty"

    def post_run_source_plugin(self):
        pass
