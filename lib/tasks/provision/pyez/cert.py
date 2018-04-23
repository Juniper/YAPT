# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import re
import threading
import time

from jnpr.junos.utils.scp import SCP
from ncclient.operations import RPCError, TimeoutExpiredError

import lib.constants as c
from lib.logmsg import LogCertTask as logmsg
from lib.logmsg import LogCommon
from lib.tasks.task import Task
from lib.tasks.tasktools import ChannelCancellation
from lib.tasks.tasktools import Configuration
from lib.tasks.tasktools import SSHPortForward
from lib.tools import Tools


class CertTask(Task):
    CHECK_SCHEMA = True
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(CertTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(CertTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        cancel_chan = ChannelCancellation()
        e = threading.Event()
        _configurator = Configuration()
        datavars = _configurator.get_config(sample_device=self.sample_device,
                                            lookup_type=c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG)

        if datavars:

            if self.grp_cfg.TASKS.Provision.Cert.PortForwarding:

                if self.sample_device.deviceSourcePlugin != c.SOURCEPLUGIN_OSSH:

                    with SCP(self.sample_device.deviceConnection, progress=False) as scp:
                        scp.put(c.conf.SERVICES.Ossh.LocalConfigFile, c.SSHD_PORT_FWD_PATH)
                        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                              logmsg.CERT_FILE_OK.format(
                                                                  self.sample_device.deviceSerial)))

                    self.sample_device.deviceConnection.close()
                    status, self.sample_device = Tools.create_dev_conn(self.sample_device)

                    if status:

                        thr = threading.Thread(target=self.do_cert_requests, args=(datavars, e, cancel_chan,))
                        thr.start()

                        sshpfwd = SSHPortForward(sample_device=self.sample_device, grp_cfg=self.grp_cfg, event=e,
                                                 cancel_chan=cancel_chan)
                        sshpfwd.init_port_fwd()

                    else:
                        return False, 'Error in device connection'

                else:

                    thr = threading.Thread(target=self.do_cert_requests, args=(datavars, e, cancel_chan,))
                    thr.start()
                    sshpfwd = SSHPortForward(sample_device=self.sample_device, grp_cfg=self.grp_cfg, event=e,
                                   cancel_chan=cancel_chan)
                    sshpfwd.init_port_fwd()

            else:
                self.do_cert_requests(datavars=datavars, event=None)

        else:
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.CERT_DEV_DATA_NOK))

    def do_cert_requests(self, datavars=None, event=None, cancel_chan=None):

        # Do time sync before getting certs
        req0 = 'set date ntp {0}'.format(datavars['device']['ntp_server'])

        req1 = 'request security pki ca-certificate enroll ca-profile ' + datavars['device']['cert'][
            'ca_profile']

        req2 = 'request security pki ca-certificate verify ca-profile ' + datavars['device']['cert'][
            'ca_profile']

        req3 = 'request security pki generate-key-pair certificate-id ' + datavars['device']['hostname'] \
               + ' size 2048 type rsa'

        req4 = 'request security pki local-certificate enroll ca-profile ' + datavars['device']['cert'][
            'ca_profile'] \
               + ' certificate-id ' + datavars['device']['hostname'] + ' domain-name ' + \
               datavars['device']['cert']['domain_name'] \
               + ' subject ' + datavars['device']['cert']['subject'] + ' challenge-password ' \
               + datavars['device']['cert']['challenge_password']

        pattern = r'(error):\s.*'
        regex = re.compile(pattern, re.MULTILINE)

        if event is not None:
            event.wait()

        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message='Request Time Sync')
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.CERT_ISSUE_CMD.format(req0))
        resp = self.sample_device.deviceConnection.cli(command=req0, format='text', warning=False)
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.CERT_ISSUE_CMD_RESP.format(req0, resp))

        try:
            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message='Request CA Cert')
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.CERT_ISSUE_CMD.format(req1))
            resp = self.sample_device.deviceConnection.cli(command=req1, format='text', warning=False)
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.CERT_ISSUE_CMD_RESP.format(req1, resp))
            status = re.findall(regex, resp)

            if len(status) > 0 and status[0] == 'error':
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=resp)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=resp)
                return

            else:
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message='Verify CA Cert')
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CERT_ISSUE_CMD.format(req2))
                resp = self.sample_device.deviceConnection.cli(command=req2, format='text', warning=False)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CERT_ISSUE_CMD_RESP.format(req2, resp))
                status = re.findall(regex, resp)

                if len(status) > 0 and status[0] == 'error':
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=status)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=status)
                    return

                else:
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message='Generate local keys')
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CERT_ISSUE_CMD.format(req3))
                    resp = self.sample_device.deviceConnection.cli(command=req3, format='text', warning=False)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CERT_ISSUE_CMD_RESP.format(req3, resp))
                    status = re.findall(regex, resp)

                    if len(status) > 0 and status[0] == 'error':
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=status)
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=status)
                        return

                    else:
                        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                               task_state_message='Request local cert')
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CERT_ISSUE_CMD.format(req4))
                        resp = self.sample_device.deviceConnection.cli(command=req4, format='text', warning=False)
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CERT_ISSUE_CMD_RESP.format(req4, resp))
                        status = re.findall(regex, resp)

                        if len(status) > 0 and status[0] == 'error':
                            self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=status)
                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=status)
                            return

                        else:
                            self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                                   task_state_message=c.TASK_STATE_MSG_DONE)
                            Tools.emit_log(task_name=self.task_name,
                                           task_state={'taskState': self.task_state,
                                                       'taskStateMsg': c.TASK_STATE_MSG_DONE},
                                           sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                           shared=self.shared,
                                           message=c.TASK_STATE_MSG_DONE,
                                           scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)
                            time.sleep(5)

                            if cancel_chan is not None:
                                cancel_chan.cancel()

        except (RPCError, TimeoutExpiredError) as err:
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.CERT_ISSUE_CMD_NOK.format(req0, err.message)))
            self.sample_device.deviceTasks.taskState[self.task_name] = err.message

    def post_run_task(self):
        pass
