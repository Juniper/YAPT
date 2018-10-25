# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import datetime
import os
import select
import socket
import threading
import lib.constants as c

from jnpr.junos.exception import *
from paramiko.ssh_exception import SSHException
from lib.logmsg import LogTaskTools as logmsg
from lib.tools import Tools


class SSHPortForward(object):
    def __init__(self, sample_device=None, grp_cfg=None, event=None, cancel_chan=None):

        self.logger = c.logger
        self.sample_device = sample_device
        self.grp_cfg = grp_cfg
        self.event = event
        self.cancel_chan = cancel_chan

        self.logger.info(Tools.create_log_msg(logmsg.SSHFWD, sample_device.deviceSerial,
                                              logmsg.SSHFWD_INIT.format(self.sample_device.deviceIP,
                                                                        grp_cfg.TASKS.Provision.Cert.LocalFwdPort,
                                                                        grp_cfg.TASKS.Provision.Cert.RemoteFwdHost,
                                                                        grp_cfg.TASKS.Provision.Cert.RemoteFwdHostPort)))

    def init_port_fwd(self):

        if self.sample_device.deviceConnection.connected:

            self.reverse_forward_tunnel(int(self.grp_cfg.TASKS.Provision.Cert.LocalFwdPort),
                                        self.grp_cfg.TASKS.Provision.Cert.RemoteFwdHost,
                                        int(self.grp_cfg.TASKS.Provision.Cert.RemoteFwdHostPort),
                                        self.sample_device.deviceConnection._conn._session.transport, self.event,
                                        self.cancel_chan)

        else:
            self.logger.info(
                Tools.create_log_msg(logmsg.SSHFWD, self.sample_device.deviceSerial, logmsg.SSHFWD_CONN_NOK))
            return False

    def reverse_forward_tunnel(self, server_port, remote_host, remote_port, transport, event, cancel_chan):

        try:

            transport.request_port_forward(address='', port=server_port, )

        except SSHException as err:
            self.logger.info(Tools.create_log_msg(logmsg.SSHFWD, self.sample_device.deviceSerial,
                                                  logmsg.SSHFWD_INIT_FAILURE.format(err.message)))

            return False, logmsg.SSHFWD_INIT_FAILURE.format(err.message)

        event.set()

        while True:

            chan = transport.accept(1)

            if cancel_chan.is_cancelled:
                break

            elif chan is None:
                continue

            thr = threading.Thread(target=self.handler, args=(chan, remote_host, remote_port,))
            thr.setDaemon(True)
            thr.start()

    def handler(self, chan, host, port):

        sock = socket.socket()
        try:
            sock.connect((host, port))

        except Exception as e:
            self.logger.info(Tools.create_log_msg(logmsg.SSHFWD, self.sample_device.deviceSerial,
                                                  logmsg.SSHFWD_REQ_FAILED.format(host, port, e)))
            return
        self.logger.info(Tools.create_log_msg(logmsg.SSHFWD, self.sample_device.deviceSerial,
                                              logmsg.SSHFWD_REQ_CONNECTED.format(chan.origin_addr, chan.getpeername(),
                                                                                 (host, port))))

        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)

            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
        sock.close()
        self.logger.info(Tools.create_log_msg(logmsg.SSHFWD, self.sample_device.deviceSerial,
                                              logmsg.SSHFWD_REQ_CLOSED.format(chan.origin_addr)))


class ChannelCancellation(object):
    def __init__(self):
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True


class Configuration:
    def __init__(self):
        self.logger = c.logger

    def prepare_device_config(self, sample_device=None):

        version = sample_device.softwareVersion
        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
        grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=sample_device.deviceGroupData)

        if c.SERVICEPLUGIN_OSSH in sample_device.deviceServicePlugin:
            sample_device.deviceConfigData['device']['ossh_secret'] = sample_device.deviceConfigData['device'][
                'ossh_secret']
            sample_device.deviceConfigData['device']['ossh_ip'] = c.conf.SERVICES.Ossh.ServiceBindAddress
            sample_device.deviceConfigData['device']['ossh_port'] = c.conf.SERVICES.Ossh.ServiceListenPort

        if sample_device.deviceConfigData:

            heading = "## Last changed: " + now + "\n"
            heading += "version " + version + ";"
            sample_device.deviceConfigData['heading'] = heading
            status, data = Tools.get_config(lookup_type=c.CONFIG_LOOKUP_TYPE_GET_TEMPLATE,
                                            sample_device=sample_device)

            if status:
                config = data.render(sample_device.deviceConfigData)
                sample_device.deviceConfiguration = config
                _device_config_file = '{0}-{1}.conf'.format(sample_device.deviceSerial, now)
                target = open(grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + _device_config_file, 'w')
                target.write(sample_device.deviceConfiguration)
                target.close()
                return {'status': True, 'sample_device': sample_device, 'configfilename': _device_config_file}

            else:
                return {'status': False, 'sample_device': sample_device, 'configfilename': data}

        else:
            self.logger.info(Tools.create_log_msg(logmsg.CONF_DEV_CFG, sample_device.deviceSerial,
                                                  logmsg.CONF_DEV_CFG_DEV_DATA_ERROR))
            return None

    def prepare_vnf_boostrap_config(self, serialnumber=None, grp_cfg=None, vnf_type=None):

        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
        status, data = Tools.get_config(lookup_type=c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG,
                                        serialnumber=None, deviceOsshId=serialnumber)

        if status:

            if vnf_type == c.VNF_TYPE_JUNIPER:
                data['device']['ossh_secret'] = data['device']['ossh_secret']
                data['device']['ossh_ip'] = c.conf.SERVICES.Ossh.ServiceBindAddress
                data['device']['ossh_port'] = c.conf.SERVICES.Ossh.ServiceListenPort

            heading = "## Last changed: " + now + "\n"
            data['heading'] = heading
            status, template = Tools.get_config(lookup_type=c.CONFIG_LOOKUP_TYPE_GET_TEMPLATE,
                                                serialnumber=None,
                                                deviceOsshId=serialnumber,
                                                path=data['yapt']['bootstrap_template_dir'],
                                                file=data['yapt']['bootstrap_template_file'])
            if status:
                config = template.render(data, deviceId=serialnumber)
                _device_config_file = '{0}-bootstrap-{1}.conf'.format(serialnumber, now)
                target = open(grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + _device_config_file, 'w')
                target.write(config)
                target.close()
                return _device_config_file

        else:
            self.logger.info(Tools.create_log_msg(logmsg.CONF_DEV_CFG, serialnumber,
                                                  logmsg.CONF_DEV_CFG_DEV_DATA_ERROR))
            return None


class Software:
    def __init__(self):
        pass

    @classmethod
    def get_software_image_name(cls, sample_device, target_version, grp_cfg):
        """
        read file names stored under local images directory, extract label and compare them with target images version
            - return local filename if we have
            - return False if we don't
        :param sample_device:
        :param target_version:
        :param grp_cfg:
        :return: filename or False
        """

        Tools.emit_log(task_name='SOFTWARE', sample_device=sample_device,
                       message=logmsg.SW_CHECK_DIR.format(target_version))
        f = False

        for filename in os.listdir(grp_cfg.TASKS.Provision.Software.ImageDir):

            if filename.endswith(".tgz"):

                local_version = re.findall(r"(?:[\d.X]+)(?:\-*)(?:[D|R\d{1}.]+)", os.path.splitext(filename)[0])[0]

                if target_version == local_version:
                    Tools.emit_log(task_name='SOFTWARE', sample_device=sample_device,
                                   message=logmsg.SW_IMAGE_OK.format(local_version))
                    f = filename
                    break
                else:
                    pass

        if not f:
            # if no file found, return False
            Tools.emit_log(task_name='SOFTWARE', sample_device=sample_device,
                           message=logmsg.SW_IMAGE_NOK.format(target_version))

        return f

    @classmethod
    def compare_device_vers_with_target_vers(cls, device_version, target_version):
        """
        Compare sample_version to target_version

        :param device_version: current installed version on device
        :param target_version: Target version which should be installed on device
        :return: if return == 0  nothing todo since same version;
                 if return == 1 nothing todo since device installed version newer;
                 if return == -1 update images since device installed version older;

        if compare every digit and they are the same till the end it indicates that they are the same
        just of different length
        """

        device_version = re.findall(r"(\d+)", device_version)
        target_version = re.findall(r"(\d+)", target_version)

        if device_version == target_version:
            return 0

        count = min(len(device_version), len(target_version))

        for x in range(count):

            if int(device_version[x]) > int(target_version[x]):

                return 1

            elif int(device_version[x]) < int(target_version[x]):

                return -1

        return 0


class Vnf(object):
    def __init__(self):
        self.logger = c.logger

    def mkdir_p(self, sftp, remote_directory):

        if remote_directory == '/':
            sftp.chdir('/')
            return
        if remote_directory == '':
            return
        try:
            sftp.chdir(remote_directory)
        except IOError:
            dirname, basename = os.path.split(remote_directory.rstrip('/'))
            Vnf.mkdir_p(self, sftp, dirname)
            sftp.mkdir(basename)
            sftp.chdir(basename)
            return True
