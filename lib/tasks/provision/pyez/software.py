# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import os
import threading
import time

from jnpr.junos import Device
from jnpr.junos import exception
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.sw import SW
from paramiko import BadHostKeyException, AuthenticationException
from scp import SCPClient

import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogSoftwareTask as logmsg
from lib.tasks.task import Task
from lib.tasks.tasktools import Software
from lib.tools import Tools


class SoftwareTask(Task):
    CHECK_SCHEMA = True
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    sample_devices = dict()
    sample_devices_lock = threading.Lock()

    def __init__(self, sample_device=None, shared=None):

        super(SoftwareTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(SoftwareTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        """
        Provision device images

        :param sample_device: A device object for which the image provisioning should be done
        :return:
        """

        target_version = getattr(self.grp_cfg.TASKS.Provision.Software.TargetVersion, self.sample_device.deviceModel,
                                 None)

        if self.sample_device.deviceStatus == c.DEVICE_STATUS_REBOOTED:

            # Device has been rebooted do not update again
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.SW_INSTALLED_VERS.format(self.sample_device.softwareVersion))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.SW_TARGET_VERS.format(target_version))
            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.SW_NO_UPDATE_NEEDED_SAME)
            self.sample_device.deviceIsRebooted = False
            self.update_task_state(new_task_state=c.TASK_STATE_DONE, task_state_message=c.TASK_STATE_MSG_DONE)

        else:

            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.SW_START_UPDATE.format(self.sample_device.deviceSerial))
            SoftwareTask.sample_devices = {self.sample_device.deviceSerial: self.sample_device}

            if target_version is not None:
                feedback = Software.compare_device_vers_with_target_vers(self.sample_device.softwareVersion,
                                                                         target_version)

                if feedback == 0:
                    self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                           task_state_message=logmsg.SW_DONE_SAME_VERS)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_INSTALLED_VERS.format(
                                       self.sample_device.softwareVersion))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_TARGET_VERS.format(target_version))
                    Tools.emit_log(task_name=self.task_name,
                                   task_state={'taskState': self.task_state, 'taskStateMsg': logmsg.SW_DONE_SAME_VERS},
                                   sample_device=self.sample_device, grp_cfg=self.grp_cfg, shared=self.shared,
                                   scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO,
                                   message=logmsg.SW_NO_UPDATE_NEEDED_SAME)

                elif feedback == 1:
                    self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                           task_state_message=logmsg.SW_DONE_DEV_NEWER_VERS)
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_INSTALLED_VERS.format(
                                       self.sample_device.softwareVersion))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_TARGET_VERS.format(target_version))
                    Tools.emit_log(task_name=self.task_name,
                                   task_state={'taskState': self.task_state,
                                               'taskStateMsg': logmsg.SW_DONE_DEV_NEWER_VERS},
                                   sample_device=self.sample_device, grp_cfg=self.grp_cfg, shared=self.shared,
                                   scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO,
                                   message=logmsg.SW_NO_UPDATE_NEEDED_NEWER)

                else:
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_INSTALLED_VERS.format(
                                       self.sample_device.softwareVersion))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_TARGET_VERS.format(target_version))
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_UPDATE_NEEDED.format(
                                       self.sample_device.softwareVersion, target_version))
                    filename = Software.get_software_image_name(self.sample_device, target_version,
                                                                grp_cfg=self.grp_cfg)

                    print filename

                    if filename:

                        full_path = self.grp_cfg.TASKS.Provision.Software.ImageDir + filename

                        if self.sample_device.deviceConnection.connected:

                            self.sample_device = self.install_device_software(full_path, filename, target_version)

                            if self.sample_device is not None:

                                if self.task_state != c.TASK_STATE_FAILED and self.task_state != c.TASK_STATE_REBOOTING:

                                    if self.sample_device.deviceConnection is not None:

                                        self.sample_device.deviceConnection.facts_refresh(keys='version')
                                        self.sample_device.softwareVersion = self.sample_device.deviceConnection.facts[
                                            "version"]
                                        self.update_task_state(new_task_state=c.TASK_STATE_DONE,
                                                               task_state_message=c.TASK_STATE_MSG_DONE)
                                        Tools.emit_log(task_name=self.task_name,
                                                       task_state={'taskState': self.task_state,
                                                                   'taskStateMsg': c.TASK_STATE_MSG_DONE},
                                                       sample_device=self.sample_device, grp_cfg=self.grp_cfg,
                                                       shared=self.shared,
                                                       scope=c.LOGGER_SCOPE_ALL, level=c.LOGGER_LEVEL_INFO,
                                                       message=logmsg.SW_NO_UPDATE_NEEDED_SAME)
                                    else:

                                        Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                                       message=logmsg.SW_CONN_NOK.format(self.sample_device.deviceIP))
                                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                               task_state_message=c.TASK_STATE_MSG_FAILED)
                                        return

                                else:
                                    return

                            else:
                                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                               message=logmsg.SW_CONN_NOK.format(self.sample_device.deviceIP))
                                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                       task_state_message=logmsg.SW_CONN_NOK.format(
                                                           self.sample_device.deviceIP))

                        else:
                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=logmsg.SW_CONN_NOK.format(self.sample_device.deviceIP))
                            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                   task_state_message=logmsg.SW_CONN_NOK.format(
                                                       self.sample_device.deviceIP))
                    else:
                        self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                               task_state_message=logmsg.SW_IMG_NOK.format(target_version))
            else:
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.SW_NO_TARGET_VERS_FOUND.format(
                                                          self.sample_device.deviceModel)))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.SW_IMG_VALUE_NOK.format(
                                           self.sample_device.deviceGroup))

    def install_device_software(self, path, image, target_version):
        """
        Call PyEz to install new JUNOS image to device
        :param sample_device:
        :param path:
        :param image:
        :return:
        """

        package = os.path.join(os.getcwd(), path)

        if c.SERVICEPLUGIN_OSSH in self.sample_device.deviceServicePlugin:

            try:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_CLEANUP_STORAGE)
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.SW_CLEANUP_STORAGE)
                self.sample_device.deviceConnection.rpc.request_system_storage_cleanup()
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_COPY_IMG.format(image))
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.SW_COPY_IMG.format(image))
                # progress = SoftwareTask.copy_progress
                with SCPClient(transport=self.sample_device.deviceConnection._conn._session.transport) as scp:
                    scp.put(package, remote_path=self.grp_cfg.TASKS.Provision.Software.RemoteDir)

            except (BadHostKeyException, AuthenticationException) as e:

                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_COPY_IMG_NOK.format(e.message))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.SW_COPY_IMG_NOK.format(e.message))
                return self.sample_device

            try:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_VERS.format(target_version))
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.SW_INSTALL_VERS.format(target_version))
                result = self.sample_device.deviceConnection.sw.pkgadd(
                    self.grp_cfg.TASKS.Provision.Software.RemoteDir + image,
                    dev_timeout=self.grp_cfg.TASKS.Provision.Software.PkgAddDevTimeout)

            except Exception as err:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_NOK.format(str(err)))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.SW_INSTALL_NOK.format(str(err)))
                return self.sample_device

            if result is True:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_OK.format(self.sample_device.deviceIP))
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.SW_INSTALL_OK.format(self.sample_device.deviceIP))

            else:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_NOK.format(str(result)))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.SW_INSTALL_NOK.format(str(result)))
                time.sleep(3)
                return self.sample_device

            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.SW_REBOOT.format(self.sample_device.deviceIP))
            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                   task_state_message=logmsg.SW_REBOOT.format(self.sample_device.deviceIP))

            try:
                rsp = self.sample_device.deviceConnection.sw.reboot()
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_REBOOT_DEV_RESP.format(rsp.replace('\n', " ")))
                self.sample_device.deviceConnection.close()
                self.sample_device.deviceIsRebooted = True
                self.update_task_state(new_task_state=c.TASK_STATE_REBOOTING,
                                       task_state_message='Rebooting...')
                c.oss_seen_devices_lck.acquire()

                try:
                    if self.sample_device.deviceIP in c.oss_seen_devices:
                        c.oss_seen_devices.pop(self.sample_device.deviceIP, None)
                finally:
                    c.oss_seen_devices_lck.release()

                return self.sample_device

            except exception.ConnectClosedError:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_CONN_LOOSE_REBOOT)
                self.update_task_state(new_task_state=c.TASK_STATE_REBOOTING,
                                       task_state_message=logmsg.SW_CONN_LOOSE_REBOOT)
                return self.sample_device

        else:

            try:

                result = self.sample_device.deviceConnection.sw.install(package=package,
                                                                        remote_path=self.grp_cfg.TASKS.Provision.Software.RemoteDir,
                                                                        cleanfs=True, no_copy=False,
                                                                        progress=SoftwareTask.install_progress)
            except Exception as err:

                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_NOK.format(str(err)))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=str(err))
                return self.sample_device

            if result is True:

                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_OK.format(self.sample_device.deviceIP))
                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                       task_state_message=logmsg.SW_INSTALL_OK.format(self.sample_device.deviceIP))

            else:

                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_INSTALL_NOK.format(str(result)))
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                       task_state_message=logmsg.SW_INSTALL_NOK.format(str(result)))
                time.sleep(3)
                return self.sample_device

            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                           message=logmsg.SW_REBOOT.format(self.sample_device.deviceIP))
            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                   task_state_message=logmsg.SW_REBOOT.format(self.sample_device.deviceIP))

            try:
                rsp = self.sample_device.deviceConnection.sw.reboot()
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_REBOOT_DEV_RESP.format(rsp.replace('\n', " ")))
                # self.sample_device.deviceConnection.close()

            except exception.ConnectClosedError:
                Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                               message=logmsg.SW_CONN_LOOSE_REBOOT)
                self.update_task_state(new_task_state=c.TASK_STATE_REBOOTING,
                                       task_state_message=logmsg.SW_CONN_LOOSE_REBOOT)
            finally:

                alive = self.probe_device_not_alive(self.sample_device,
                                                    self.grp_cfg.TASKS.Provision.Software.RetryProbeCounter)

                if not alive:
                    self.sample_device.deviceIsRebooted = True
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_PROBE_WAKEUP.format(self.sample_device.deviceIP))
                    status, self.sample_device = Tools.create_dev_conn(self.sample_device, connect=False)

                    if status:

                        alive = self.probe_device_alive(self.sample_device,
                                                        self.grp_cfg.TASKS.Provision.Software.RebootProbeTimeout)

                        if alive:

                            Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                           message=logmsg.SW_PROBE_WAKUP_OK.format(self.sample_device.deviceIP))
                            self.sample_device.deviceIsRebooted = False
                            self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                                   task_state_message=logmsg.SW_PROBE_WAKUP_OK.format(
                                                       self.sample_device.deviceIP))
                            status, self.sample_device = Tools.create_dev_conn(self.sample_device)

                            if status:

                                self.sample_device.deviceConnection.bind(cu=Config, sw=SW)
                                # Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                #               message=logmsg.SW_CONN_OK.format(self.sample_device.deviceIP))
                                self.update_task_state(new_task_state=c.TASK_STATE_PROGRESS,
                                                       task_state_message=logmsg.SW_CONN_OK.format(
                                                           self.sample_device.deviceIP))

                                return self.sample_device

                            else:
                                return self.sample_device

                        else:
                            self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                                   task_state_message=c.TASK_STATE_MSG_FAILED)
                            self.sample_device.deviceConnection = None
                            return self.sample_device

                else:
                    Tools.emit_log(task_name=self.task_name, sample_device=self.sample_device,
                                   message=logmsg.SW_PROBE_DEV_NOK.format(self.sample_device.deviceIP,
                                                                          self.grp_cfg.TASKS.Provision.Software.RebootProbeCounter))
                    self.update_task_state(new_task_state=c.TASK_STATE_FAILED,
                                           task_state_message=logmsg.SW_PROBE_DEV_NOK.format(
                                               self.sample_device.deviceIP,
                                               self.grp_cfg.TASKS.Provision.Software.RebootProbeCounter))

    def probe_device_alive(self, device, timeout):
        """

        :param device:
        :param timeout:
        :return:
        """

        alive = device.deviceConnection.probe(timeout=5)
        probe_attemps = self.grp_cfg.TASKS.Provision.Software.RebootProbeCounter
        probe_cntr = 0

        while not alive:

            if probe_cntr <= probe_attemps:
                alive = device.deviceConnection.probe(timeout)
                probe_cntr += 1
                Tools.emit_log(task_name=self.task_name, sample_device=device,
                               message=logmsg.SW_PROBE_DEV.format(timeout))
                self.update_task_state(new_task_state=c.TASK_STATE_REBOOTING,
                                       task_state_message=logmsg.SW_PROBE_WAIT_REBOOT.format(str(probe_cntr)))
            else:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_FAILED)
                break

        return alive

    def probe_device_not_alive(self, device, timeout):
        """

        :param device:
        :param timeout:
        :return:
        """

        alive = device.deviceConnection.probe(timeout=5)
        probe_attemps = self.grp_cfg.TASKS.Provision.Software.RebootProbeCounter
        probe_cntr = 0

        while alive:

            if probe_cntr <= probe_attemps:
                alive = device.deviceConnection.probe(1)
                probe_cntr += 1
                Tools.emit_log(task_name=self.task_name, sample_device=device,
                               message=logmsg.SW_PROBE_DEV.format(timeout))
                self.update_task_state(new_task_state=c.TASK_STATE_REBOOTING,
                                       task_state_message=logmsg.SW_PROBE_WAIT_REBOOT.format(str(probe_cntr)))
                time.sleep(timeout)
            else:
                self.update_task_state(new_task_state=c.TASK_STATE_FAILED, task_state_message=c.TASK_STATE_MSG_FAILED)
                break

        return alive

    @staticmethod
    def install_progress(dev, report):
        c.logger.info(
            '[{0:{1}}][{2:{3}}][{4}]'.format('SOFTWARE', c.FIRST_PAD, dev.facts["serialnumber"], c.SECOND_PAD, report))
        SoftwareTask.sample_devices[dev.facts['serialnumber']].deviceTasks.taskState['Software'] = {
            'taskState': c.TASK_STATE_PROGRESS, 'taskStateMsg': report}

    @staticmethod
    def copy_progress(filename, size, sent):
        # print filename + " " + str(int(size)) + " " + str(int(sent))
        # print (sent / (1024 * 1024)) * 100.0 / (size / (1024 * 1024))

        c.logger.info('PROVSW: Copy file <%s> progress <%s>', filename,
                      (sent / (1024 * 1024)) * 100.0 / (size / (1024 * 1024)))
        # SoftwareTask.sample_devices[dev.facts['serialnumber']].deviceTasks.taskState['Software'] = (sent / (1024 * 1024)) * 100.0 / (size / (1024 * 1024)))

    def post_run_task(self):
        with SoftwareTask.sample_devices_lock:
            if self.sample_device.deviceSerial in SoftwareTask.sample_devices:
                del SoftwareTask.sample_devices[self.sample_device.deviceSerial]
