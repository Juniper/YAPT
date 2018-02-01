# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import sys

from isc_dhcp_leases.iscdhcpleases import IscDhcpLeases

from lib.plugins.sourceplugin import SourcePlugin
from lib.sampledevice import SampleDevice
from lib.logmsg import LogSourcePlg as logmsg
from lib.logmsg import LogCommon
import lib.constants as c
from lib.tools import Tools


class Dhcp(SourcePlugin):
    def __init__(self, plugin_cfg=None):

        super(Dhcp, self).__init__(plugin_cfg=plugin_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.DHCP_PLG, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Dhcp, SourcePlugin))))
        self.logfile = getattr(c.conf.SERVICES, (plugin_cfg['pluginName']).title()).LogFile

    def pre_run_source_plugin(self):
        pass

    def run_source_plugin(self, timestamp):
        """
        :return: raw_devices
        """

        try:

            log_content = IscDhcpLeases(self.logfile)
            current_devices = log_content.get_current()

            if len(current_devices) > 0:

                for device in current_devices:
                    yield SampleDevice(deviceIP=current_devices[device].ip, deviceTimeStamp=timestamp,
                                       deviceStatus=c.DEVICE_STATUS_NEW, deviceSourcePlugin=c.SOURCEPLUGIN_DHCP)

        except IOError:
            self.logger.info('PROVLOG: Can\'t open logfile: %s ', self.logfile)
            sys.exit()

    def post_run_source_plugin(self):
        pass
