# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#


from jnpr.junos.utils.scp import SCP
from paramiko.sftp_client import SFTPClient

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import Logvnfstage as logmsg
from lib.tasks.task import Task
from lib.tasks.tasktools import Configuration
from lib.tasks.tasktools import Vnf
from lib.tools import Tools


class VnfstageTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(VnfstageTask, self).__init__(sample_device=sample_device, shared=shared)
        self.task_type = c.TASK_TYPE_PROVISION
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(VnfstageTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        # this task has to run before configuration task
        # copy base image
        # make copy of base image for specific VNF
        # generate bootstrap conf
        # copy boostrap conf
        # make bootstrap iso
        # Done

        _vnf = Vnf()
        _configurator = Configuration()
        datavars = self.sample_device.deviceConfigData

        if datavars:

            for vnf in datavars['device']['vnfs']:

                self.logger.info(
                    Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial, logmsg.VNFSTAGE_SETUP_DIR))
                sftp = SFTPClient.from_transport(self.sample_device.deviceConnection._conn._session._transport)
                _vnf.mkdir_p(sftp, vnf['bootstrap_remote_dir'] + vnf['name'])

                # Copy base image and boostrap conf
                try:
                    with SCP(self.sample_device.deviceConnection, progress=False) as scp:
                        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                               task_state_message=logmsg.VNFSTAGE_CP_BASE_IMG.format(vnf['base_img'],
                                                                                                     self.sample_device.deviceIP,
                                                                                                     vnf[
                                                                                                         'base_img_path']))
                        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                              logmsg.VNFSTAGE_CP_BASE_IMG.format(vnf['base_img'],
                                                                                                 self.sample_device.deviceIP,
                                                                                                 vnf['base_img_path'])))
                        scp.put('images/' + vnf['base_img'], vnf['base_img_path'])
                        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                              logmsg.VNFSTAGE_MAKE_CP_BASE_IMG_OK.format(vnf['name'])))
                        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                              logmsg.VNFSTAGE_GEN_BOOTSTRAP.format(vnf['name'])))

                except OSError as ose:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.VNFSTAGE_CP_ERR.format(vnf['name'], ose.strerror,
                                                                                            ose.filename))
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.VNFSTAGE_CP_ERR.format(vnf['name'], ose.strerror,
                                                                                        ose.filename)))
                    return

                vnf_conf_file = _configurator.prepare_vnf_boostrap_config(serialnumber=vnf['deviceID'], grp_cfg=self.grp_cfg,
                                                                          vnf_type=vnf['vnf_type'])

                if vnf_conf_file is not None:

                    full_path = self.grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + vnf_conf_file

                    with SCP(self.sample_device.deviceConnection, progress=False) as scp:
                        self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                               task_state_message=logmsg.VNFSTAGE_COPY_BOOTSTRAP.format(full_path,
                                                                                                        self.sample_device.deviceIP,
                                                                                                        vnf[
                                                                                                            'bootstrap_remote_dir'] +
                                                                                                        vnf[
                                                                                                            'name'] + '/'))
                        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                              logmsg.VNFSTAGE_COPY_BOOTSTRAP.format(full_path,
                                                                                                    self.sample_device.deviceIP,
                                                                                                    vnf[
                                                                                                        'bootstrap_remote_dir'] +
                                                                                                    vnf['name'] + '/')))

                        try:

                            scp.put(full_path, vnf['bootstrap_remote_dir'] + vnf['name'] + '/' + 'juniper.conf')
                            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                                  logmsg.VNFSTAGE_COPY_BOOTSTRAP_OK.format(
                                                                      vnf['name'])))

                        except OSError as ose:
                            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                   task_state_message=logmsg.VNFSTAGE_CP_ERR.format(vnf['name'],
                                                                                                    ose.strerror,
                                                                                                    ose.filename))
                            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                                  logmsg.VNFSTAGE_CP_ERR.format(vnf['name'],
                                                                                                ose.strerror,
                                                                                                ose.filename)))
                            return

                    # Make copy of base image
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message=logmsg.VNFSTAGE_MAKE_CP_BASE_IMG.format(vnf['name']))
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.VNFSTAGE_MAKE_CP_BASE_IMG.format(vnf['name'])))
                    req1 = '{0} {1}{2} {3}{4}{5}'.format('file copy', vnf['base_img_path'], vnf['base_img'],
                                                         vnf['base_img_path'], vnf['name'], '.qcow2')
                    self.sample_device.deviceConnection.cli(command=req1, format='text', warning=False)
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.VNFSTAGE_MAKE_CP_BASE_IMG_OK.format(vnf['name'])))
                    # Genisoimage
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message=logmsg.VNFSTAGE_GEN_BOOTSTRAP.format(vnf['name']))
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.VNFSTAGE_GEN_BOOTSTRAP.format(vnf['name'])))
                    req2 = '{0} {1}{2}{3}{4} {5}{6}{7}{8}{9}'.format('request genisoimage', vnf['bootstrap_remote_dir'],
                                                                     vnf['name'], '/', 'juniper.conf',
                                                                     vnf['bootstrap_remote_dir'], vnf['name'], '/',
                                                                     vnf['name'], '.iso')
                    self.sample_device.deviceConnection.cli(command=req2, format='text', warning=False)
                    self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                           task_state_message=logmsg.VNFSTAGE_BOOSTRAP_OK.format(vnf['name']))
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.VNFSTAGE_BOOSTRAP_OK.format(vnf['name'])))
                else:
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=c.TASK_STATE_MSG_FAILED)
                    return

                self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                       task_state_message=c.TASK_STATE_MSG_DONE)

        else:
            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                   task_state_message=logmsg.VNFSTAGE_DEV_CONF_READ_ERR)
            self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                  logmsg.VNFSTAGE_DEV_CONF_READ_ERR))
            return

    def post_run_task(self):
        pass
