# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import datetime
import os
import select
import socket
import threading
import jsonpickle
import yaml

from jnpr.junos.exception import *
from paramiko.ssh_exception import SSHException
from lib.amqp.amqpmessage import AMQPMessage
from lib.processor import BackendClientProcessor

import lib.constants as c
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
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)

    def prepare_device_config(self, sample_device=None, grp_cfg=None):

        version = sample_device.softwareVersion
        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')

        if c.SOURCEPLUGIN_OSSH in sample_device.deviceSourcePlugin:
            sample_device.deviceConfigData['device']['ossh_secret'] = sample_device.deviceConfigData['device'][
                'ossh_secret']
            sample_device.deviceConfigData['device']['ossh_ip'] = c.conf.SERVICES.Ossh.ServiceBindAddress
            sample_device.deviceConfigData['device']['ossh_port'] = c.conf.SERVICES.Ossh.ServiceListenPort

        if sample_device.deviceConfigData:

            heading = "## Last changed: " + now + "\n"
            heading += "version " + version + ";"
            sample_device.deviceConfigData['heading'] = heading
            template = self.get_config(lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_GET_TEMPLATE,
                                       sample_device=sample_device, grp_cfg=grp_cfg)
            if template is not None:
                config = template.render(sample_device.deviceConfigData)
                sample_device.deviceConfiguration = config
                _device_config_file = '{0}-{1}.conf'.format(sample_device.deviceSerial, now)
                target = open(grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + _device_config_file, 'w')
                target.write(sample_device.deviceConfiguration)
                target.close()
                return {'sample_device': sample_device, 'configfilename': _device_config_file}

        else:
            self.logger.info(Tools.create_log_msg(logmsg.CONF_DEV_CFG, sample_device.deviceSerial,
                                                  logmsg.CONF_DEV_CFG_DEV_DATA_ERROR))
            return None

    def prepare_vnf_boostrap_config(self, serialnumber=None, grp_cfg=None, vnf_type=None):

        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
        datavars = self.get_config(lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_GET_DEVICE,
                                   serialnumber=None, deviceOsshId=serialnumber)

        if datavars:

            if vnf_type == c.VNF_TYPE_JUNIPER:
                datavars['device']['ossh_secret'] = datavars['device']['ossh_secret']
                datavars['device']['ossh_ip'] = c.conf.SERVICES.Ossh.ServiceBindAddress
                datavars['device']['ossh_port'] = c.conf.SERVICES.Ossh.ServiceListenPort

            heading = "## Last changed: " + now + "\n"
            datavars['heading'] = heading
            template = self.get_config(lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_TEMPLATE_BOOTSTRAP,
                                       serialnumber=None,
                                       deviceOsshId=serialnumber,
                                       path=datavars['yapt']['bootstrap_template_dir'],
                                       file=datavars['yapt']['bootstrap_template_file'])

            if template:
                config = template.render(datavars, deviceId=serialnumber)
                _device_config_file = '{0}-bootstrap-{1}.conf'.format(serialnumber, now)
                target = open(grp_cfg.TASKS.Provision.Configuration.ConfigFileHistory + _device_config_file, 'w')
                target.write(config)
                target.close()
                return _device_config_file

        else:
            self.logger.info(Tools.create_log_msg(logmsg.CONF_DEV_CFG, serialnumber,
                                                  logmsg.CONF_DEV_CFG_DEV_DATA_ERROR))
            return None

    def get_config(self, lookup_type=None, **kvargs):
        """
        obtain specific config type <lookup_type> from configured source in <DeviceConfSrcPlugins>
        :param lookup_type: defines which data we looking for e.g. device_data / group_data / template
        :return:
        """

        config_source_plugins = Tools.load_dev_cfg_src_plugins()

        if 'sample_device' in kvargs:
            sample_device = kvargs.get('sample_device')
            sn = sample_device.deviceSerial
            osshid = sample_device.deviceOsshId
            deviceGroup = sample_device.deviceGroup

        elif 'serialnumber' and 'deviceOsshId' in kvargs:
            sn = kvargs.get('serialnumber')
            osshid = kvargs.get('deviceOsshId')

        elif 'deviceGroup' in kvargs:
            deviceGroup = kvargs.get('deviceGroup')
            sn = deviceGroup
            osshid = None

        else:
            return None

        self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                          logmsg.CONF_SOURCE_PLG_LOAD.format(config_source_plugins))

        # check ooba
        if c.conf.SOURCE.DeviceConfOoba:
            self.logger.info(Tools.create_log_msg(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                                  'Checking config id mapping in asset database'))
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_GET_BY_SERIAL,
                                  payload=sn if sn else osshid,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload:
                self.logger.info(Tools.create_log_msg(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                                      'Successfully retrieved config id mapping for {0}<-->{1}'.format(
                                                          sn, response.payload)))

                sn = response.payload

        if config_source_plugins:

            for config_source_plugin in config_source_plugins:

                source = config_source_plugins[config_source_plugin]
                self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                  logmsg.CONF_SOURCE_PLG_FOUND.format(config_source_plugin))
                source = getattr(source.pop(), config_source_plugin.title())
                self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                  logmsg.CONF_SOURCE_PLG_LOADED.format(config_source_plugin))
                source = source()

                if lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_DEVICE:
                    isFile, datavars = source.get_config_data(serialnumber=sn, deviceOsshId=osshid)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:
                        self.logger.info(
                            Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                 logmsg.CONF_VALIDATE_INIT.format('device')))
                        resp, err = source.validate(source=datavars, lookup_type=lookup_type)

                        if resp:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                                  logmsg.CONF_VALIDATE_OK.format('Device')))
                            return datavars
                        else:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                                  logmsg.CONF_VALIDATE_NOK.format(err)))
                            break
                    else:
                        continue

                elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_DEVICE_FILE:

                    isFile, filename = source.get_config_data_file(serialnumber=sn, deviceOsshId=osshid)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:
                        self.logger.info(
                            Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                 logmsg.CONF_VALIDATE_INIT.format('device')))
                        resp, err = source.validate(source=filename, lookup_type=lookup_type)

                        if resp:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                                  logmsg.CONF_VALIDATE_OK.format('Device')))
                            return filename
                        else:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                                  logmsg.CONF_VALIDATE_NOK.format('Device', err)))
                            break
                    else:
                        continue

                elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_TEMPLATE:

                    isFile, template = source.get_config_template_data(serialnumber=sn,
                                                                  grp_cfg=kvargs.get('grp_cfg'))
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:
                        return template
                    else:
                        continue

                elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_TEMPLATE_FILE:

                    isFile, template = source.get_config_template_file(serialnumber=sn,
                                                                       grp_cfg=kvargs.get('grp_cfg'))
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:
                        return template
                    else:
                        continue

                elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_TEMPLATE_BOOTSTRAP:

                    isFile, template = source.get_bootstrap_config_template(serialnumber=osshid,
                                                                            path=kvargs.get('path'),
                                                                            file=kvargs.get('file'))
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:
                        return template
                    else:
                        continue

                elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_GROUP:
                    isFile, groupvars = source.get_group_data(serialnumber=sn, group=deviceGroup)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:

                        self.logger.info(
                            Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                 logmsg.CONF_VALIDATE_INIT.format('group')))

                        resp, err = source.validate(source=groupvars, lookup_type=lookup_type)

                        if resp:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                                  logmsg.CONF_VALIDATE_OK.format('Group')))
                            return groupvars
                        else:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, sn if sn else osshid,
                                                                  logmsg.CONF_VALIDATE_NOK.format('Group', err)))
                            break
                    else:
                        continue

                elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_GROUP_FILE:
                    isFile, filename = source.get_group_data_file(serialnumber=sn, group=deviceGroup)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, sn if sn else osshid,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(config_source_plugin))

                    if isFile:
                        return filename
                    else:
                        continue

            return None

        else:
            self.logger.info(logmsg.CONF_SOURCE_PLG, sn if sn else osshid, 'Config Source plugin sequence empty')
            return

    def add_config(self, lookup_type=None, **kvargs):

        if lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_ADD_TEMPLATE:

            if 'templateName' and 'templateData' and 'groupName' and 'configSource' in kvargs:

                templateName = kvargs.get('templateName')
                templateData = kvargs.get('tempateData')
                groupName = kvargs.get('groupName')
                configSource = kvargs.get('configSource')

                if templateName and templateData and groupName and configSource:

                    source = Tools.load_dev_cfg_src_plugin(name=configSource)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                      logmsg.CONF_SOURCE_PLG_FOUND.format(configSource))
                    source = getattr(source, configSource.title())
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                      logmsg.CONF_SOURCE_PLG_LOADED.format(configSource))
                    source = source()

                    if source:

                        isFile, datavars = source.add_config_template_data(templateName=templateName,
                                                                           templateData=templateData,
                                                                           group=groupName)
                        self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                          logmsg.CONF_SOURCE_PLG_EXEC.format(configSource))

                        return isFile, datavars
                    else:
                        self.logger.info(logmsg.CONF_SOURCE_PLG, groupName,
                                         logmsg.CONF_SOURCE_PLG_NOK.format(configSource))

        elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_ADD_GROUP:

            if 'groupName' and 'groupData' and 'configSource' in kvargs:

                groupName = kvargs.get('groupName')
                groupData = kvargs.get('groupData')
                configSource = kvargs.get('configSource')

                if groupName and groupData and configSource:

                    source = Tools.load_dev_cfg_src_plugin(name=configSource)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                      logmsg.CONF_SOURCE_PLG_FOUND.format(configSource))
                    source = getattr(source, configSource.title())
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                      logmsg.CONF_SOURCE_PLG_LOADED.format(configSource))
                    source = source()

                    if source:

                        self.logger.info(
                            Tools.create_log_msg(logmsg.CONF_VALIDATE, groupName,
                                                 logmsg.CONF_VALIDATE_INIT.format('group')))
                        resp, err = source.validate(source=yaml.safe_load(groupData), lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_ADD_GROUP)

                        if resp:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, groupName,
                                                                  logmsg.CONF_VALIDATE_OK.format('Group')))

                            isFile, datavars = source.add_group_data(groupName=groupName,
                                                                     groupData=groupData)
                            self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                              logmsg.CONF_SOURCE_PLG_EXEC.format(configSource))

                            return isFile, datavars

                        else:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, groupName,
                                                                  logmsg.CONF_VALIDATE_NOK.format(err)))
                            return False, 'Validation of group file <{0}> failed with error <{1}>'.format(groupName, err)
                    else:
                        self.logger.info(logmsg.CONF_SOURCE_PLG, groupName,
                                         logmsg.CONF_SOURCE_PLG_NOK.format(configSource))

        else:
            return False, 'Unknown lookup type'

    def del_config(self, lookup_type=None, **kvargs):

        if lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_DEL_GROUP:

            groupName = kvargs.get('groupName')
            configSource = kvargs.get('groupConfigSource')

            if groupName and configSource:

                source = Tools.load_dev_cfg_src_plugin(name=configSource)
                self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                  logmsg.CONF_SOURCE_PLG_FOUND.format(configSource))
                source = getattr(source, configSource.title())
                self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                  logmsg.CONF_SOURCE_PLG_LOADED.format(configSource))
                source = source()

                if source:

                    isFile, datavars = source.del_group_data(groupName=groupName, )
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, groupName,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(configSource))

                    return isFile, datavars

                else:
                    self.logger.info(logmsg.CONF_SOURCE_PLG, groupName,
                                     logmsg.CONF_SOURCE_PLG_NOK.format(configSource))

        elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_DEL_TEMPLATE:

            templateName = kvargs.get('templateName')
            templateDevGrp = kvargs.get('templateDevGrp')
            configSource = kvargs.get('templateConfigSource')

            if templateName and templateDevGrp and configSource:

                source = Tools.load_dev_cfg_src_plugin(name=configSource)
                self.logger.debug(logmsg.CONF_SOURCE_PLG, templateName,
                                  logmsg.CONF_SOURCE_PLG_FOUND.format(configSource))
                source = getattr(source, configSource.title())
                self.logger.debug(logmsg.CONF_SOURCE_PLG, templateName,
                                  logmsg.CONF_SOURCE_PLG_LOADED.format(configSource))
                source = source()

                if source:

                    isFile, datavars = source.del_config_template_data(templateName=templateName, group=templateDevGrp)
                    self.logger.debug(logmsg.CONF_SOURCE_PLG, templateName,
                                      logmsg.CONF_SOURCE_PLG_EXEC.format(configSource))
                    return isFile, datavars

                else:
                    self.logger.info(logmsg.CONF_SOURCE_PLG, templateName,
                                     logmsg.CONF_SOURCE_PLG_NOK.format(configSource))

        else:
            return False, 'Unknown lookup type'


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

                local_version = re.findall(r"(?:[\d.X]+)(?:\-*)(?:[D\d.]+)", filename)[0]

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
