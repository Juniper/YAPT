# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import collections
import getpass
import importlib
import inspect
import os
import re
import sys

import jnpr.junos.exception
import jsonpickle
import napalm
import requests
import ruamel.yaml
import yaml
from cryptography.fernet import Fernet
from jnpr.junos import Device
from napalm_base import NetworkDriver

import constants as c
from lib.logmsg import LogTools as logmsg
from lib.objectstore import ObjectView

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

requests.packages.urllib3.disable_warnings()


class Tools:
    """
    Common class for the YAPT environment.
    Provides common methods for provisioning, config file reading, version checking, etc.
    """

    @classmethod
    def create_log_msg(cls, name, devid, message):

        if devid is None:

            header = '[{0:{1}}][{2:{3}}]'.format(name.upper(), c.FIRST_PAD, c.FILL_PAD, c.SECOND_PAD)
            return '{0}[{1}]'.format(header, message)

        else:
            header = '[{0:{1}}][{2:{3}}]'.format(name.upper(), c.FIRST_PAD, devid, c.SECOND_PAD)
            return '{0}[{1}]'.format(header, message)

    @classmethod
    def create_amqp_startup_log(cls, exchange=None, type=None, routing_key=None, host=None, channel=None):

        frame = inspect.stack()[1][0]
        caller_name = Tools.get_class_from_frame(frame)
        c.logger.debug(Tools.create_log_msg(logmsg.AMQP, caller_name,
                                            logmsg.AMQP_INIT.format(exchange, type, routing_key, host,
                                                                    str(channel))))

    @classmethod
    def create_config_view(cls, config_type=None, filename=None, stream=None):

        if config_type == c.CONFIG_TYPE_MAIN:

            try:

                c.conf = ObjectView(yaml.safe_load(open(c.YAPT_CONF_FILE).read()))

            except IOError as ioe:
                print Tools.create_log_msg(logmsg.YAPT_CONF, '',
                                           logmsg.YAPT_CONF_LOAD_ERR.format(ioe.strerror, ioe.filename))
                sys.exit()

        elif config_type == c.CONFIG_TYPE_GROUP:

            if filename:
                try:
                    return ObjectView(yaml.safe_load(open(c.conf.STORAGE.Local.DeviceGrpFilesDir + filename).read()))

                except IOError as ioe:
                    c.logger.info(Tools.create_log_msg(logmsg.YAPT_CONF, '', logmsg.__format__(filename, ioe.message)))
                    return
            else:
                return ObjectView(stream)

    @classmethod
    def create_master_key(cls):
        from ruamel.yaml.util import load_yaml_guess_indent

        _datavars, ind, bsi = ruamel.yaml.util.load_yaml_guess_indent(
            open('../../' + c.YAPT_MASTER_KEY_FILE))

        if _datavars['MasterKey'] is not None:
            print 'There is already a master key'

        else:
            _datavars['MasterKey'] = Fernet.generate_key()
            ruamel.yaml.round_trip_dump(_datavars, open('../../' + c.YAPT_MASTER_KEY_FILE, 'w'),
                                        indent=ind, block_seq_indent=bsi)

    @classmethod
    def create_password(cls, pwd_type=None):
        from ruamel.yaml.util import load_yaml_guess_indent

        _datavars, ind, bsi = ruamel.yaml.util.load_yaml_guess_indent(
            open('../../' + c.YAPT_CONF_FILE))

        with open('../../' + c.YAPT_MASTER_KEY_FILE, 'r') as f:
            mkey = yaml.load(f)

        if pwd_type == c.YAPT_PASSWORD_TYPE_DEVICE:
            p = getpass.getpass(prompt='Enter ' + pwd_type + ' secret: ')
            q = getpass.getpass(prompt='Confirm ' + pwd_type + ' secret: ')
            if p == q:
                _datavars['COMMON']['DevicePwd'] = Fernet(mkey['MasterKey']).encrypt(p)
        elif pwd_type == c.YAPT_PASSWORD_TYPE_OSSH:
            p = getpass.getpass(prompt='Enter ' + pwd_type + ' secret: ')
            q = getpass.getpass(prompt='Confirm ' + pwd_type + ' secret: ')
            if p == q:
                _datavars['SERVICES']['Ossh']['SharedSecret'] = Fernet(mkey['MasterKey']).encrypt(p)
        elif pwd_type == c.YAPT_PASSWORD_TYPE_SPACE:
            p = getpass.getpass(prompt='Enter ' + pwd_type + ' secret: ')
            q = getpass.getpass(prompt='Confirm ' + pwd_type + ' secret: ')
            if p == q:
                _datavars['JUNOSSPACE']['Password'] = Fernet(mkey['MasterKey']).encrypt(p)
        elif pwd_type == c.YAPT_PASSWORD_TYPE_AMQP:
            p = getpass.getpass(prompt='Enter ' + pwd_type + ' secret: ')
            q = getpass.getpass(prompt='Confirm ' + pwd_type + ' secret: ')
            if p == q:
                _datavars['AMQP']['Password'] = Fernet(mkey['MasterKey']).encrypt(p)
        else:
            c.logger.info('Unknown password type')

        ruamel.yaml.round_trip_dump(_datavars, open('../../conf/yapt/yapt.yml', 'w'),
                                    indent=ind, block_seq_indent=bsi)

    @classmethod
    def create_dev_conn(cls, sample_device=None, connect=True):
        """
        Creates a device connection object according to driver settings. If an OSSH session is used hand over sock_fd.
        :param sample_device. Create a connection object for sample_device.
        :return Device. Return Device object with with the according connection
        """

        if c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_PYEZ:
            # If we get an ossh connection hand over sock_fd
            if c.SERVICEPLUGIN_OSSH == sample_device.deviceServicePlugin:
                if c.conf.COMMON.DevicePwdIsRsa:

                    dev_conn = Device(host=None, sock_fd=sample_device.deviceConnection, user=c.conf.COMMON.DeviceUsr,
                                      password=Tools.get_password(c.YAPT_PASSWORD_TYPE_DEVICE_RSA),
                                      gather_facts=False)

                    if dev_conn is not None:

                        if connect:
                            try:
                                dev_conn.open()
                                sample_device.deviceConnection = dev_conn
                                return True, sample_device

                            except jnpr.junos.exception.ConnectError as err:
                                c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                                   logmsg.CONN_MGMT_OPEN_FAILED.format(err)))
                                return False, err
                        else:
                            sample_device.deviceConnection = dev_conn
                            return True, sample_device
                else:

                    dev_conn = Device(host=None, sock_fd=sample_device.deviceConnection, user=c.conf.COMMON.DeviceUsr,
                                      password=Tools.get_password(c.YAPT_PASSWORD_TYPE_DEVICE), gather_facts=False)

                    if dev_conn is not None:
                        if connect:
                            try:
                                dev_conn.open()
                                sample_device.deviceConnection = dev_conn
                                return True, sample_device

                            except jnpr.junos.exception.ConnectError as err:
                                c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                                   logmsg.CONN_MGMT_OPEN_FAILED.format(err)))
                                return False, err
                        else:
                            sample_device.deviceConnection = dev_conn
                            return True, sample_device
            else:
                if c.conf.COMMON.DevicePwdIsRsa:
                    dev_conn = Device(host=sample_device.deviceIP, user=c.conf.COMMON.DeviceUsr,
                                      ssh_private_key_file=Tools.get_password(c.YAPT_PASSWORD_TYPE_DEVICE_RSA))

                    if connect:
                        c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                           logmsg.CONN_MGMT_PROBING_DEV.format(sample_device.deviceIP,
                                                                                               c.conf.COMMON.ConnectionProbeTimeout)))
                        probe = dev_conn.probe(timeout=c.conf.COMMON.ConnectionProbeTimeout)

                        if probe:
                            c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                               logmsg.CONN_MGMT_PROBING_OK.format(
                                                                   sample_device.deviceIP,
                                                                   c.conf.COMMON.ConnectionProbeTimeout)))
                            try:
                                dev_conn.open()
                                sample_device.deviceConnection = dev_conn
                                return True, sample_device

                            except jnpr.junos.exception.ConnectError as err:
                                c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                                   logmsg.CONN_MGMT_OPEN_FAILED.format(err)))
                                return False, err

                        else:
                            c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                               logmsg.CONN_MGMT_PROBING_FAILED.format(
                                                                   sample_device.deviceIP)))
                            return False, Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                               logmsg.CONN_MGMT_PROBING_FAILED.format(
                                                                   sample_device.deviceIP))

                    else:
                        sample_device.deviceConnection = dev_conn
                        return True, sample_device

                else:
                    dev_conn = Device(host=sample_device.deviceIP, user=c.conf.COMMON.DeviceUsr,
                                      password=Tools.get_password(c.YAPT_PASSWORD_TYPE_DEVICE),
                                      port=c.conf.DEVICEDRIVER.Pyez.port,
                                      gather_facts=False)

                    if connect:
                        c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceSerial,
                                                           logmsg.CONN_MGMT_PROBING_DEV.format(sample_device.deviceIP,
                                                                                               c.conf.COMMON.ConnectionProbeTimeout)))
                        probe = dev_conn.probe(timeout=c.conf.COMMON.ConnectionProbeTimeout)

                        if probe:
                            c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceSerial,
                                                               logmsg.CONN_MGMT_PROBING_OK.format(
                                                                   sample_device.deviceIP,
                                                                   c.conf.COMMON.ConnectionProbeTimeout)))
                            try:
                                dev_conn.open()
                                sample_device.deviceConnection = dev_conn
                                return True, sample_device

                            except jnpr.junos.exception.ConnectError as err:
                                c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                                   logmsg.CONN_MGMT_OPEN_FAILED.format(err)))
                                return False, err

                        else:
                            c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceSerial,
                                                               logmsg.CONN_MGMT_PROBING_FAILED.format(
                                                                   sample_device.deviceIP)))
                            return False, Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceSerial,
                                                               logmsg.CONN_MGMT_PROBING_FAILED.format(
                                                                   sample_device.deviceIP))
                    else:
                        sample_device.deviceConnection = dev_conn
                        return True, sample_device

        elif c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_NAPALM:
            # Use the appropriate network driver to connect to the device
            driver = napalm.base.get_network_driver(c.conf.DEVICEDRIVER.Napalm.Module)
            # Connect
            dev_conn = driver(hostname=sample_device.deviceIP, username=c.conf.COMMON.DeviceUsr,
                              password=Tools.get_password(c.YAPT_PASSWORD_TYPE_DEVICE),
                              optional_args={'port': c.conf.DEVICEDRIVER.Napalm.Port})

            try:

                sample_device.deviceConnection = dev_conn
                dev_conn.open()
                return True, sample_device

            except (napalm.base.exceptions.ConnectionException, napalm.base.exceptions.ConnectAuthError,
                    jnpr.junos.exception.ConnectError) as err:
                c.logger.info(Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                   logmsg.CONN_MGMT_OPEN_FAILED.format(err)))
                return False, Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                                   logmsg.CONN_MGMT_OPEN_FAILED.format(err))

        else:
            c.logger.info(
                Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP, logmsg.CONN_MGMT_DEV_DRIVER_NOK))
            return False, Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP,
                                               logmsg.CONN_MGMT_DEV_DRIVER_NOK)

    @classmethod
    def get_device_facts(cls, sample_device=None):

        if sample_device is not None:
            if isinstance(sample_device.deviceConnection, NetworkDriver):

                facts = sample_device.deviceConnection.get_facts()
                sample_device.deviceName = facts["hostname"]
                sample_device.deviceModel = facts["model"]
                sample_device.deviceSerial = facts["serial_number"]
                sample_device.softwareVersion = facts["os_version"]
                config = sample_device.deviceConnection.get_config()
                curr_conf = config['running']
                sample_device.deviceConfiguration = curr_conf

                return sample_device

            elif isinstance(sample_device.deviceConnection, jnpr.junos.device.Device):

                sample_device.deviceName = sample_device.deviceConnection.facts['hostname']
                sample_device.deviceModel = sample_device.deviceConnection.facts['model']

                if not sample_device.deviceConnection.facts['personality'] == 'NFX':
                    sample_device.deviceSerial = sample_device.deviceConnection.facts['serialnumber']

                sample_device.softwareVersion = sample_device.deviceConnection.facts['version']
                config = sample_device.deviceConnection.rpc.get_config(options={'format': 'text'})
                curr_conf = config.text.encode('ascii', 'replace')
                sample_device.deviceConfiguration = curr_conf
                return sample_device

            else:

                c.logger.info(
                    Tools.create_log_msg(logmsg.CONN_MGMT, sample_device.deviceIP, logmsg.CONN_MGMT_DEV_DRIVER_NOK))

        else:
            c.logger.info('Not a device instance')

    @classmethod
    def get_task_module_from_group(cls, grp_cfg=None, task_name=None):

        task = getattr(grp_cfg.TASKS.Provision, task_name, None)

        if getattr(task, 'Module', None):
            return getattr(task, 'Module', None)

        else:
            return task_name

    @classmethod
    def get_task_descent_from_cls(cls, module_name=None, path=None):

        _module = importlib.import_module(module_name, package=path.replace("/", "."))
        cls_name = '{0}Task'.format(module_name.rsplit('.', 1)[1].title())
        task_name = module_name.rsplit('.', 1)[1].title()

        _task = getattr(_module, cls_name, None)
        task_descent = getattr(_task, 'TASK_DESCENT', None)

        if task_descent:
            return task_descent

        else:
            return task_name

    @classmethod
    def get_task_plugins(cls):
        """
        Get all available provisioning task plugins in according plugin directory and determine task descent
        :return: list of available task plugins
        """

        plugins = list()

        if c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_PYEZ:

            task_re = re.compile('.py$', re.IGNORECASE)

            for p in c.TASK_PLG_PYEZ_DIRS:

                importlib.import_module(p.replace("/", "."))
                plugin_files = filter(task_re.search, os.listdir('{0}{1}'.format(p, '/')))
                _module = lambda fp: '.' + os.path.splitext(fp)[0]
                tasks = map(_module, plugin_files)

                for task in tasks:

                    if not task.startswith('.__') and not task.startswith('.task'):
                        task_name = Tools.get_task_descent_from_cls(module_name=task, path=p)
                        plugins.append(task_name)

            return set(plugins)

        elif c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_NAPALM:

            task_re = re.compile('.py$', re.IGNORECASE)

            for p in c.TASK_PLG_NAPALM_DIRS:

                importlib.import_module(p.replace("/", "."))
                plugin_files = filter(task_re.search, os.listdir('{0}{1}'.format(p, '/')))
                _module = lambda fp: '.' + os.path.splitext(fp)[0]
                tasks = map(_module, plugin_files)

                for task in tasks:
                    if not task.startswith('.__') and not task.startswith('.task'):
                        task_name = Tools.get_task_descent_from_cls(module_name=task, path=p)
                        plugins.append(task_name)

            return set(plugins)

    @classmethod
    def get_class_from_frame(cls, fr):
        args, _, _, value_dict = inspect.getargvalues(fr)
        # we check the first parameter for the frame function is
        # named 'self'
        if len(args) and args[0] == 'self':
            # in that case, 'self' will be referenced in value_dict
            instance = value_dict.get('self', None)
            if instance:
                # return its class
                return getattr(instance, '__class__', None).__name__
        # return None otherwise
        return None

    @classmethod
    def get_password(cls, pwd_type=None):

        with open(c.YAPT_MASTER_KEY_FILE, 'r') as f:
            mkey = yaml.load(f)

        if pwd_type == c.YAPT_PASSWORD_TYPE_DEVICE:
            return Fernet(mkey['MasterKey']).decrypt(c.conf.COMMON.DevicePwd)
        elif pwd_type == c.YAPT_PASSWORD_TYPE_DEVICE_RSA:
            return 'conf/yapt/id_rsa'
        elif pwd_type == c.YAPT_PASSWORD_TYPE_OSSH:
            return Fernet(mkey['MasterKey']).decrypt(c.conf.SERVICES.Ossh.SharedSecret)
        elif pwd_type == c.YAPT_PASSWORD_TYPE_SPACE:
            return Fernet(mkey['MasterKey']).decrypt(c.conf.JUNOSSPACE.Password)
        elif pwd_type == c.YAPT_PASSWORD_TYPE_AMQP:
            return Fernet(mkey['MasterKey']).decrypt(c.conf.AMQP.Password)
        else:
            c.logger.info('Unknown password type')

    @classmethod
    def get_config(self, lookup_type=None, **kvargs):
        """
        obtain specific config type <lookup_type> from configured source in <DeviceConfSrcPlugins>
        :param lookup_type: defines which data we looking for e.g. device_data / group_data / template
        :return:
        """

        osshid = None
        isRaw = None
        templateName = None
        groupName = None

        from lib.pluginfactory import StoragePlgFact
        storageFact = StoragePlgFact()
        storage_plgs = storageFact.init_plugins()

        c.logger.debug(Tools.create_log_msg('TOOLS', 'get_config', kvargs))

        if 'sample_device' in kvargs:
            sample_device = kvargs.get('sample_device')
            sn = sample_device.deviceSerial
            osshid = sample_device.deviceOsshId
            groupName = sample_device.deviceGroup
            templateName = sample_device.deviceTemplate

        elif 'serialnumber' in kvargs and 'deviceOsshId' in kvargs:
            sn = kvargs.get('serialnumber')
            osshid = kvargs.get('deviceOsshId')

        elif 'templateName' in kvargs and 'groupName' in kvargs and 'isRaw' in kvargs:
            templateName = kvargs.get('templateName')
            groupName = kvargs.get('groupName')
            isRaw = kvargs.get('isRaw')
            sn = templateName

        elif 'groupName' in kvargs and 'isRaw' in kvargs:
            groupName = kvargs.get('groupName')
            isRaw = kvargs.get('isRaw')
            sn = groupName

        elif 'configSerial' in kvargs and 'isRaw' in kvargs:
            sn = kvargs.get('configSerial')
            isRaw = kvargs.get('isRaw')

        else:
            return False, 'Parameters not matching'

        c.logger.debug(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                            logmsg.STORAGE_PLG_LOAD.format(c.conf.STORAGE.DeviceConfSrcPlugins)))

        if c.conf.STORAGE.DeviceConfSrcPlugins:
            for key, storage in storage_plgs.iteritems():
                if lookup_type == c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG:
                    # check ooba
                    if c.conf.STORAGE.DeviceConfOoba:
                        c.logger.info(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                           'Checking config id mapping in asset database'))

                        from lib.amqp.amqpmessage import AMQPMessage
                        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_REST_ASSET_GET_BY_SERIAL,
                                              payload=osshid if osshid else sn,
                                              source=c.AMQP_PROCESSOR_REST)

                        from lib.processor import BackendClientProcessor
                        _backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
                        response = _backendp.call(message=message)
                        response = jsonpickle.decode(response)

                        # Check if mapping found
                        if response.payload[0]:

                            c.logger.info(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                               'Successfully retrieved config id mapping for {0}<-->{1}'.format(
                                                                   osshid if osshid else sn, response.payload[1])))
                            sn = response.payload[1]

                        else:
                            c.logger.info(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                               'Failed to retrieve config id mapping for {0}<-->{1}'.format(
                                                                   sn, response.payload)))
                            return response.payload[0], response.payload[1]

                    status, data = storage.get_device_config_data(serialnumber=sn, isRaw=isRaw)

                    if status:
                        return status, data
                    else:
                        continue

                elif lookup_type == c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG_FILE:

                    status, filename = storage.get_device_config_data_file(serialnumber=sn, deviceOsshId=osshid)
                    c.logger.debug(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                        logmsg.STORAGE_PLG_EXEC.format(storage)))

                    if status:
                        return status, filename
                    else:
                        continue

                elif lookup_type == c.CONFIG_LOOKUP_TYPE_GET_TEMPLATE:

                    if sn and templateName and groupName:

                        isFile, template = storage.get_config_template_data(serialnumber=sn,
                                                                            templateName=templateName,
                                                                            groupName=groupName, isRaw=isRaw)
                        c.logger.debug(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                            logmsg.STORAGE_PLG_EXEC.format(storage)))

                        if isFile:
                            return isFile, template
                        else:
                            c.logger.info(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                               logmsg.STORAGE_TEMPLATE_NOK(templateName, templateName)))
                            continue

                elif lookup_type == c.CONFIG_LOOKUP_TYPE_GET_TEMPLATE_FILE:

                    if sn and templateName:

                        isFile, template = storage.get_config_template_file(serialnumber=sn,
                                                                            templateName=templateName,
                                                                            groupName=groupName)
                        c.logger.debug(logmsg.STORAGE_PLG, sn if sn else osshid,
                                       logmsg.STORAGE_PLG_EXEC.format(storage))

                        if isFile:
                            return isFile, template
                        else:
                            continue

                elif lookup_type == c.CONFIG_LOOKUP_TYPE_TEMPLATE_BOOTSTRAP:

                    if osshid:

                        isFile, template = storage.get_bootstrap_config_template(serialnumber=osshid,
                                                                                 path=kvargs.get('path'),
                                                                                 file=kvargs.get('file'))
                        c.logger.debug(logmsg.STORAGE_PLG, sn if sn else osshid,
                                       logmsg.STORAGE_PLG_EXEC.format(storage))

                        if isFile:
                            return template
                        else:
                            continue

                elif lookup_type == c.CONFIG_LOOKUP_TYPE_GET_GROUP:

                    if sn and groupName:

                        status, groupvars = storage.get_group_data(serialnumber=sn, groupName=groupName, isRaw=isRaw)
                        c.logger.debug(Tools.create_log_msg(logmsg.STORAGE_PLG, sn if sn else osshid,
                                                            logmsg.STORAGE_PLG_EXEC.format(storage)))

                        if status:
                            return True, groupvars
                        else:
                            continue

                elif lookup_type == c.CONFIG_LOOKUP_TYPE_GET_GROUP_FILE:

                    if sn and groupName:

                        isFile, filename = storage.get_group_data_file(serialnumber=sn, group=groupName)
                        c.logger.debug(logmsg.STORAGE_PLG, sn if sn else osshid,
                                       logmsg.STORAGE_PLG_EXEC.format(storage))

                        if isFile:
                            return filename
                        else:
                            continue

            return False, 'No device or group or template data found'

        else:
            c.logger.info(logmsg.STORAGE_PLG, sn if sn else osshid, 'Config Source plugin sequence empty')
            return

    @classmethod
    def load_factory(cls, fact_name=None):
        """Import class by its fully qualified name.
        """

        p, m = fact_name.rsplit('.', 1)

        try:
            module = importlib.import_module(p)

        except ImportError as ie:
            Tools.create_log_msg('IMPORTCLS', None, ie.message)
            return

        if module:

            my_class = getattr(module, m, None)
            return my_class
        else:
            return

    @classmethod
    def load_task_plugins(cls, sequence):
        """
               Load provision and external provision task plugins.
               First load provision plugins then load external plugins. Plugin name has to be unique.
               :return: task_plugins
               """

        if c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_PYEZ:

            task_plugins = dict()
            task_re = re.compile('.py$', re.IGNORECASE)
            pluginfiles = filter(task_re.search, os.listdir(os.path.join(os.path.dirname(__file__),
                                                                         'tasks/provision/' + c.YAPT_DEVICE_DRIVER_PYEZ + '/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, pluginfiles)
            importlib.import_module('lib.tasks.provision.' + c.YAPT_DEVICE_DRIVER_PYEZ)

            for task in tasks:

                if not task.startswith('.__') or task.startswith('task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task,
                                                    package="lib.tasks.provision." + c.YAPT_DEVICE_DRIVER_PYEZ)}

            pluginfiles = filter(task_re.search,
                                 os.listdir(os.path.join(os.path.dirname(__file__), 'tasks/provision/external/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, pluginfiles)
            importlib.import_module('lib.tasks.provision.external')

            for task in tasks:

                if not task.startswith('.__') and not task.startswith('task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task, package="lib.tasks.provision.external")}

            pluginfiles = filter(task_re.search,
                                 os.listdir(os.path.join(os.path.dirname(__file__), 'tasks/verification/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, pluginfiles)
            importlib.import_module('lib.tasks.verification')

            for task in tasks:
                if not task.startswith('.__') and not task.startswith('.task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {importlib.import_module(task, package="lib.tasks.verification")}

            return task_plugins

        elif c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_NAPALM:

            task_plugins = dict()
            task_re = re.compile('.py$', re.IGNORECASE)
            pluginfiles = filter(task_re.search,
                                 os.listdir(os.path.join(os.path.dirname(__file__),
                                                         'tasks/provision/' + c.YAPT_DEVICE_DRIVER_NAPALM + '/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, pluginfiles)
            importlib.import_module('lib.tasks.provision.' + c.YAPT_DEVICE_DRIVER_NAPALM)

            for task in tasks:

                if not task.startswith('.__') or task.startswith('task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task,
                                                    package="lib.tasks.provision." + c.YAPT_DEVICE_DRIVER_NAPALM)}

            pluginfiles = filter(task_re.search,
                                 os.listdir(os.path.join(os.path.dirname(__file__), 'tasks/provision/external/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, pluginfiles)
            importlib.import_module('lib.tasks.provision.external')

            for task in tasks:

                if not task.startswith('.__') or task.startswith('.task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task, package="lib.tasks.provision.external")}

            return task_plugins
        else:

            c.logger.info('Unknown device driver type')

    @classmethod
    def load_provision_task_plugin(cls, task_name):

        if c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_PYEZ:
            task_re = re.compile('.py$', re.IGNORECASE)
            plugin_files = None

            for p in c.TASK_PLG_PYEZ_DIRS:

                try:
                    plugin_files = filter(task_re.search, os.listdir('{0}{1}'.format(p, '/')))

                except OSError as ose:
                    c.logger.info(Tools.create_log_msg('TASKPLUGINLDR', None, ose))

                _module = lambda fp: '.' + os.path.splitext(fp)[0]
                tasks = map(_module, plugin_files)
                importlib.import_module(p.replace('/', '.'))

                for task in tasks:

                    if not task.startswith('.__') or task.startswith('task'):

                        if task[1:].title() == task_name:
                            m = importlib.import_module(task, package=p.replace('/', '.'))
                            return getattr(m, '{0}Task'.format(task_name), None)

        else:
            importlib.import_module('lib.tasks.provision.' + c.YAPT_DEVICE_DRIVER_NAPALM)

    @classmethod
    def load_provision_task_plugins(cls, sequence):
        """
        Load provision and external provision task plugins.
        First load provision plugins then load external plugins. Plugin name has to be unique.
        :return: task_plugins
        """

        if c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_PYEZ:

            task_plugins = dict()
            task_re = re.compile('.py$', re.IGNORECASE)
            plugin_files = filter(task_re.search, os.listdir(os.path.join(os.path.dirname(__file__),
                                                                          'tasks/provision/' + c.YAPT_DEVICE_DRIVER_PYEZ + '/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, plugin_files)
            importlib.import_module('lib.tasks.provision.' + c.YAPT_DEVICE_DRIVER_PYEZ)

            for task in tasks:

                if not task.startswith('.__') or task.startswith('task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task,
                                                    package="lib.tasks.provision." + c.YAPT_DEVICE_DRIVER_PYEZ)}

            plugin_files = filter(task_re.search,
                                  os.listdir(os.path.join(os.path.dirname(__file__), 'tasks/provision/external/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, plugin_files)
            importlib.import_module('lib.tasks.provision.external')

            for task in tasks:

                if not task.startswith('.__') and not task.startswith('task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task, package="lib.tasks.provision.external")}

            return task_plugins

        elif c.conf.DEVICEDRIVER.Driver == c.YAPT_DEVICE_DRIVER_NAPALM:

            task_plugins = dict()
            task_re = re.compile('.py$', re.IGNORECASE)
            plugin_files = filter(task_re.search,
                                  os.listdir(os.path.join(os.path.dirname(__file__),
                                                          'tasks/provision/' + c.YAPT_DEVICE_DRIVER_NAPALM + '/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, plugin_files)
            importlib.import_module('lib.tasks.provision.' + c.YAPT_DEVICE_DRIVER_NAPALM)

            for task in tasks:

                if not task.startswith('.__') or task.startswith('task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task,
                                                    package="lib.tasks.provision." + c.YAPT_DEVICE_DRIVER_NAPALM)}

            plugin_files = filter(task_re.search,
                                  os.listdir(os.path.join(os.path.dirname(__file__), 'tasks/provision/external/')))
            # Todo: Replace lambda?
            _module = lambda fp: '.' + os.path.splitext(fp)[0]
            tasks = map(_module, plugin_files)
            importlib.import_module('lib.tasks.provision.external')

            for task in tasks:

                if not task.startswith('.__') or task.startswith('.task'):

                    if task[1:].title() in sequence:
                        plugin_name = task[1:].title()
                        task_plugins[plugin_name] = {
                            importlib.import_module(task, package="lib.tasks.provision.external")}

            return task_plugins
        else:

            c.logger.info('Unknown device driver type')

    @classmethod
    def load_verification_plugins(cls, sequence):
        """
        Load provision and external verification plugins. First load provision adapter then load external plugins.
        Plugin name has to be unique.
        :return: verification_plugins
        """

        verification_plugins = dict()
        task_re = re.compile('.py$', re.IGNORECASE)
        pluginfiles = filter(task_re.search, os.listdir(os.path.join(os.path.dirname(__file__), 'tasks/verification/')))
        # Todo: Replace lambda?
        _module = lambda fp: '.' + os.path.splitext(fp)[0]
        tasks = map(_module, pluginfiles)
        importlib.import_module('lib.tasks.verification')

        for task in tasks:
            if not task.startswith('.__') and not task.startswith('.task'):

                if task[1:].title() in sequence:
                    plugin_name = task[1:].title()
                    verification_plugins[plugin_name] = {
                        importlib.import_module(task, package="lib.tasks.verification")}

        return verification_plugins

    @classmethod
    def load_service_normalizer(cls, service):

        svc_re = re.compile('.py$', re.IGNORECASE)
        plugin_files = None

        try:
            plugin_files = filter(svc_re.search, os.listdir('{0}'.format('lib/services/normalizer')))

        except OSError as ose:
            c.logger.info(Tools.create_log_msg('NORMALIZERLDR', None, ose))

        _module = lambda fp: '.' + os.path.splitext(fp)[0]
        normalizer = map(_module, plugin_files)
        importlib.import_module('lib.services.normalizer')

        for n in normalizer:

            if not n.startswith('.__') or n.startswith('task'):

                if n[1:].title() == service:
                    m = importlib.import_module(n, package='lib.services.normalizer')
                    return getattr(m, '{0}'.format(service), None)

    @classmethod
    def load_backend_plugins(cls):

        log_re = re.compile('.py$', re.IGNORECASE)
        pluginfiles = filter(log_re.search, os.listdir(os.path.join(os.path.dirname(__file__), 'backend')))
        _module = lambda fp: '.' + os.path.splitext(fp)[0]
        plugins = map(_module, pluginfiles)
        importlib.import_module('lib.backend')
        backend_plugins = dict()

        for plugin in plugins:

            if not plugin.startswith('.__') and not plugin.startswith('.backend'):
                plugin_name = plugin[1:]
                backend_plugins[plugin_name] = {importlib.import_module(plugin, package="lib.backend")}

        return backend_plugins

    @classmethod
    def load_space_plugins(cls):

        log_re = re.compile('.py$', re.IGNORECASE)
        pluginfiles = filter(log_re.search, os.listdir(os.path.join(os.path.dirname(__file__), 'space')))
        _module = lambda fp: '.' + os.path.splitext(fp)[0]
        plugins = map(_module, pluginfiles)
        importlib.import_module('lib.space')
        space_plugins = dict()

        for plugin in plugins:

            if not plugin.startswith('.__') and not plugin.startswith('.src'):
                plugin_name = plugin[1:]
                space_plugins[plugin_name] = {importlib.import_module(plugin, package="lib.space")}

        return space_plugins

    @classmethod
    def load_storage_plugins(cls):

        log_re = re.compile('.py$', re.IGNORECASE)
        pluginfiles = filter(log_re.search, os.listdir(os.path.join(os.path.dirname(__file__), 'storage')))
        _module = lambda fp: '.' + os.path.splitext(fp)[0]
        plugins = map(_module, pluginfiles)
        importlib.import_module('lib.storage')
        storage_plugins = dict()

        for plugin in plugins:

            if not plugin.startswith('.__') and not plugin.startswith('.base'):

                if plugin[1:].title() in c.conf.STORAGE.DeviceConfSrcPlugins:
                    plugin_name = plugin[1:]
                    storage_plugins[plugin_name] = {importlib.import_module(plugin, package="lib.storage")}

        return storage_plugins

    @classmethod
    def load_storage_plugin(cls, name):
        importlib.import_module('lib.storage')
        plugin = importlib.import_module('.' + name.lower(), package="lib.storage")
        return plugin

    @classmethod
    def load_emitter_plugins(cls):

        log_re = re.compile('.py$', re.IGNORECASE)
        pluginfiles = filter(log_re.search, os.listdir(os.path.join(os.path.dirname(__file__), 'emitter')))
        _module = lambda fp: '.' + os.path.splitext(fp)[0]
        plugins = map(_module, pluginfiles)
        importlib.import_module('lib.emitter')
        emitter_plugins = collections.OrderedDict()

        for plugin in plugins:

            if not plugin.startswith('.__') and not plugin.startswith('.emitter'):

                if plugin[1:] in c.conf.EMITTER.Plugins:
                    plugin_name = plugin[1:]
                    emitter_plugins[plugin_name] = {importlib.import_module(plugin, package="lib.emitter")}

        return emitter_plugins

    @classmethod
    def amqp_send_to_logger(cls, routing_key=None, body_decoded=None):

        frame = inspect.stack()[1][0]
        caller_name = Tools.get_class_from_frame(frame)

        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', '#' * 60))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Routing-Key: {0}".format(routing_key)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Message: {0}".format(type(body_decoded))))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Message from: {0}".format(body_decoded.source)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Message type: {0}".format(body_decoded.message_type)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', '#' * 60))

    @classmethod
    def amqp_receive_to_logger(cls, routing_key=None, body_decoded=None):

        frame = inspect.stack()[1][0]
        caller_name = Tools.get_class_from_frame(frame)

        c.logger.debug(Tools.create_log_msg(caller_name, 'Received', '#' * 60))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Received', "Routing-Key: {0}".format(routing_key)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Received', "Message: {0}".format(type(body_decoded))))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Received', "Message from: {0}".format(body_decoded.source)))
        c.logger.debug(
            Tools.create_log_msg(caller_name, 'Received', "Message type: {0}".format(body_decoded.message_type)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Received', '#' * 60))

    @classmethod
    def amqp_send_error_to_logger(cls, routing_key=None, body_decoded=None):

        frame = inspect.stack()[1][0]
        caller_name = Tools.get_class_from_frame(frame)
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', '#' * 60))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Something is wrong with message to be send"))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Routing-Key: {0}".format(routing_key)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Message: {0}".format(type(body_decoded))))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Message Type: {0}".format(body_decoded.message_type)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', "Message Source: {0}".format(body_decoded.source)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Send', '#' * 60))

    @classmethod
    def amqp_receive_error_to_logger(cls, routing_key=None, body_decoded=None):

        frame = inspect.stack()[1][0]
        caller_name = Tools.get_class_from_frame(frame)

        c.logger.debug(Tools.create_log_msg(caller_name, 'Receive', '#' * 60))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Receive', "Something is wrong with received message"))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Receive', "Received Routing-Key: {0}".format(routing_key)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Receive', "Message: {0}".format(type(body_decoded))))
        c.logger.debug(
            Tools.create_log_msg(caller_name, 'Receive', "Message Type: {0}".format(body_decoded.message_type)))
        c.logger.debug(Tools.create_log_msg(caller_name, 'Receive', "Message Source: {0}".format(body_decoded.source)))
        c.logger.debug(Tools.create_log_msg(caller_name, "Receive", '#' * 60))

    @classmethod
    def emit_log(cls, task_name=None, task_state=None, sample_device=None, grp_cfg=None, shared=None, message=None,
                 scope=c.LOGGER_SCOPE_LOCAL, level=c.LOGGER_LEVEL_INFO):

        if scope == c.LOGGER_SCOPE_ALL:

            for log_plg_name, log_plg in c.active_log_plgs.iteritems():
                log_plg.emit(task_name=task_name, task_state=task_state, sample_device=sample_device, grp_cfg=grp_cfg,
                             shared=shared, message=message, level=level)

        elif scope == c.LOGGER_SCOPE_LOCAL:

            c.active_log_plgs['Local'].emit(task_name=task_name, sample_device=sample_device, grp_cfg=grp_cfg,
                                            shared=shared,
                                            message=message, level=level)
