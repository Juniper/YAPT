# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


import datetime
import time

from jinja2 import TemplateNotFound
from jnpr.junos.exception import *
from ncclient.operations.errors import TimeoutExpiredError

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogConfigurationTask as logmsg
from lib.tasks.task import Task
from lib.tasks.tasktools import Configuration
from lib.tools import Tools


class InternalTask(Task):
    CHECK_SCHEMA = True
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0
    TASK_DESCENT = 'Configuration'

    def __init__(self, sample_device=None, shared=None):

        super(InternalTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(InternalTask, Task))))
        self._device_config_file = None

    def pre_run_task(self):
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                              'Processing task dependencies: {0}'.format(
                                                  self.grp_cfg.TASKS.Provision.Configuration.Dependencies)))

        if self.grp_cfg.TASKS.Provision.Configuration.Dependencies:

            for dep in self.grp_cfg.TASKS.Provision.Configuration.Dependencies:
                task_dep = getattr(self, 'dep_configuration_{0}'.format(dep.lower()))
                task_dep()

    def run_task(self):

        """
        Provision device config

        :param sample_device: A device object for which the config provisioning should be done
        :return:
        """
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message=logmsg.CONF_TASK_INIT.format(self.sample_device.deviceSerial))
        configurator = Configuration()
        resp = configurator.prepare_device_config(sample_device=self.sample_device)

        if resp['status']:

            self._device_config_file = resp['configfilename']

            if self.sample_device.deviceConnection.connected:

                # Lock the configuration, load configuration changes, and commit
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message=logmsg.CONF_TASK_LOCK)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_LOCK)

                try:

                    self.sample_device.deviceConnection.cu.lock()
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message=logmsg.CONF_TASK_LOCK_OK)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_LOCK_OK)

                except LockError as err:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.CONF_TASK_LOCK_NOK.format(err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_LOCK_NOK.format(err.message))

                    return

                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.CONF_TASK_LOAD)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_LOAD)

                try:

                    self.sample_device.deviceConnection.cu.load(
                        path=self.grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + self._device_config_file,
                        merge=self.grp_cfg.TASKS.Provision.Configuration.Merge,
                        overwrite=self.grp_cfg.TASKS.Provision.Configuration.Overwrite)

                except (ConfigLoadError, ValueError, Exception) as err:
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_LOAD_NOK.format(err))
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.CONF_TASK_LOAD_NOK.format(err))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_UNLOCK)

                    try:

                        self.sample_device.deviceConnection.cu.unlock()
                        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                               task_state_message=logmsg.CONF_TASK_UNLOCK_OK)
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CONF_TASK_UNLOCK_OK)

                    except UnlockError:
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=logmsg.CONF_TASK_UNLOCK_NOK.format(err))
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CONF_TASK_UNLOCK_NOK.format(err))

                    return

                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message=logmsg.CONF_TASK_COMMIT)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_COMMIT)

                try:

                    self.sample_device.deviceConnection.cu.commit(
                        timeout=self.grp_cfg.TASKS.Provision.Configuration.Internal.CommitTimeout,
                        comment='Commit by YAPT at {0}'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H%M')),
                        confirm=int(self.grp_cfg.TASKS.Provision.Configuration.Internal.ConfirmedTimeout))
                    self.sample_device.deviceConnection.cu.commit(
                        timeout=self.grp_cfg.TASKS.Provision.Configuration.Internal.CommitTimeout,
                        comment='Commit confirmed by YAPT at {0}'.format(
                            datetime.datetime.now().strftime('%Y-%m-%d-%H%M')))

                    if not self.sample_device.deviceModel.startswith(
                            'NFX') or not self.sample_device.deviceModel.startswith('VQFX'):
                        self.sample_device.deviceConnection.cu.rescue('save')

                except (CommitError, ConnectClosedError, RpcTimeoutError, TimeoutExpiredError) as err:

                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message=logmsg.CONF_TASK_COMMIT_NOK.format(err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_COMMIT_NOK.format(err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_UNLOCK)

                    try:

                        self.sample_device.deviceConnection.cu.unlock()
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=c.TASK_STATE_MSG_FAILED)
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CONF_TASK_UNLOCK_OK)

                    except (UnlockError, ConnectClosedError) as err:
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=c.TASK_STATE_MSG_FAILED)
                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                       message=logmsg.CONF_TASK_UNLOCK_NOK.format(err.message))
                    return

                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS, task_state_message=logmsg.CONF_TASK_UNLOCK)
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_UNLOCK)

                try:
                    self.sample_device.deviceConnection.cu.unlock()
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message=logmsg.CONF_TASK_UNLOCK_OK)
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.CONF_TASK_UNLOCK_OK))

                except UnlockError as err:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.CONF_TASK_UNLOCK_NOK.format(err.message))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.CONF_TASK_UNLOCK_NOK.format(err.message))
                    return

                # If refreshing facts on NFX it needs more time doing so after configuration commit
                if self.sample_device.deviceModel.startswith('NFX'):
                    time.sleep(15)
                self.sample_device.deviceConnection.facts_refresh(keys='hostname')
                self.sample_device.deviceName = self.sample_device.deviceConnection.facts['hostname']
                self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)
                Tools.emit_log(task_name=self.task_name,
                               task_state={'taskState': self.task_state,
                                           'taskStateMsg': c.TASK_STATE_MSG_DONE},
                               sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                               shared=self.shared, message=logmsg.CONF_TASK_COMMIT_OK.format(self._device_config_file),
                               scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO)

            else:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.CONF_TASK_CONN_NOK.format(
                                           self.sample_device.deviceSerial))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_CONN_NOK.format(self.sample_device.deviceSerial))

        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                   task_state_message=logmsg.CONF_TASK_CFG_TEMPLATE_ERROR.format(
                                       '', '', resp['configfilename']))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.CONF_TASK_CFG_TEMPLATE_ERROR.format('', '', resp['configfilename']))

    def post_run_task(self):
        pass

    def dep_configuration_cert(self):

        self.logger.info(
            Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                 'Processing configuration task deps for cert task'))

        if self.grp_cfg.TASKS.Provision.Cert.PortForwarding:

            try:

                eurl = self.grp_cfg.TASKS.Provision.Cert.EnrollmentUrl
                rurl = self.grp_cfg.TASKS.Provision.Cert.RevocationUrl
                eurl = 'http://{0}:{1}/{2}'.format(self.sample_device.deviceIP,
                                                   str(self.grp_cfg.TASKS.Provision.Cert.LocalFwdPort), eurl)
                rurl = 'http://{0}:{1}/{2}'.format(self.sample_device.deviceIP,
                                                   str(self.grp_cfg.TASKS.Provision.Cert.LocalFwdPort), rurl)
                self.sample_device.deviceConfigData['device']['cert']['enrollment_url'] = eurl
                self.sample_device.deviceConfigData['device']['cert']['revocation_url'] = rurl

            except (TemplateNotFound, IOError) as err:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.CONF_TASK_CFG_TEMPLATE_ERROR.format(err.errno,
                                                                                                     err.strerror,
                                                                                                     err.filename))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_CFG_TEMPLATE_ERROR.format(err.errno, err.strerror,
                                                                                  err.filename))
                return None

        else:

            try:

                eurl = self.grp_cfg.TASKS.Provision.Cert.EnrollmentUrl
                rurl = self.grp_cfg.TASKS.Provision.Cert.RevocationUrl
                eurl = 'http://{0}:{1}/{2}'.format(self.grp_cfg.TASKS.Provision.Cert.RemoteFwdHost,
                                                   str(self.grp_cfg.TASKS.Provision.Cert.RemoteFwdHostPort), eurl)
                rurl = 'http://{0}:{1}/{2}'.format(self.grp_cfg.TASKS.Provision.Cert.RemoteFwdHost,
                                                   str(self.grp_cfg.TASKS.Provision.Cert.RemoteFwdHostPort), rurl)
                self.sample_device.deviceConfigData['device']['cert']['enrollment_url'] = eurl
                self.sample_device.deviceConfigData['device']['cert']['revocation_url'] = rurl

            except (TemplateNotFound, IOError) as err:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.CONF_TASK_CFG_TEMPLATE_ERROR.format(err.errno,
                                                                                                     err.strerror,
                                                                                                     err.filename))
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.CONF_TASK_CFG_TEMPLATE_ERROR.format(err.errno, err.strerror,
                                                                                  err.filename))
                return None

    def dep_configuration_ipam(self):
        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                               task_state_message='Processing configuration task deps for ipam task')
        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                       message='Processing configuration task deps for ipam task')
        self.sample_device.deviceConfigData['ipam'] = dict()

        for idx, ip in enumerate(self.shared[c.TASK_SHARED_IPAM]):
            self.sample_device.deviceConfigData['ipam']['IP' + str(idx)] = ip[0]
