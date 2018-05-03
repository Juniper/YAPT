# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import lib.constants as c

from lib.tasks.task import Task
from lib.tools import Tools


class VpnVerifyTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_VERIFICATION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(VpnVerifyTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug('Subclass: %s', issubclass(VpnVerifyTask, Task))
        self.logger.debug('Instance: %s', isinstance(VpnVerifyTask, Task))

    def pre_run_task(self):
        pass

    def run_task(self):

        if self.sample_device.deviceConnection.connected:

            self.sample_device.deviceVerificationTasksStates['Vpn'] = 'Getting VPN info'
            result = self.sample_device.deviceConnection.rpc.get_ike_security_associations_information()

            for item in result.findall(".//ike-sa-remote-address"):

                if item.text == self.grp_cfg.VERIFICATION.Vpn.SaRemoteAddress:

                    self.logger.info('VerifyVpn-[%s]: Found VPN. Checking status...', self.sample_device.deviceIP)
                    self.sample_device.deviceVerificationTasksStates['Vpn'] = 'Got VPN info'
                    state = result.findtext(".//ike-sa-state")

                    if state == 'UP':

                        self.sample_device.deviceVerificationTasksStates['Vpn'] = 'VPN is Up'

                        result = self.sample_device.deviceConnection.rpc.ping(
                            host=self.grp_cfg.VERIFICATION.Ping.Destination,
                            count=self.grp_cfg.VERIFICATION.Ping.Count)

                        pktloss = result.findtext('.//packet-loss').lstrip('\n').strip('\n')

                        if pktloss == '0':

                            self.logger.info('VerifyPing-[%s]: Ping test successfull', self.sample_device.deviceIP)
                            self.sample_device.deviceVerificationTasksStates['Ping'] = 'Ping test successful'

                        else:
                            self.logger.info('VerifyPing-[%s]: ping test failed', self.sample_device.deviceIP)
                            self.sample_device.deviceVerificationTasksStates['Ping'] = 'Ping test failed'
                    else:
                        self.logger.info('VerifyVpn-[%s]: VPN is down', self.sample_device.deviceIP)
                        self.sample_device.deviceVerificationTasksStates['Vpn'] = 'VPN is Down'
                else:
                    self.logger.info('VerifyVpn-[%s]: No VPN found', self.sample_device.deviceIP)
                    self.sample_device.deviceVerificationTasksStates['Vpn'] = 'Failed'
        else:

            self.logger.info('VerifyVpn-[%s]: Error in device connection', self.sample_device.deviceIP)

    def post_run_task(self):
        pass
