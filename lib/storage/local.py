# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#

import os

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from lib.storage.base import Storage
import lib.constants as c
from lib.logmsg import LogLocal as logmsg
from lib.tools import Tools


class Local(Storage):

    def __init__(self):
        super(Local, self).__init__()

    def get_config_template_file(self, serialnumber=None, templateName=None, groupName=None):

        status, data = self.get_group_data(serialnumber=serialnumber, groupName=groupName)

        if status:
            grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=data)
            t_dir = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir
            t_file = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile

            if os.path.exists(t_dir + t_file) and os.path.isfile(t_dir + t_file):
                self.logger.info(Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_TEMPLATE_FILE_OK.format(
                    t_dir + t_file)))
                return True, t_dir + t_file
            else:
                self.logger.info(Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_TEMPLATE_FILE_NOK.format(
                    t_dir + t_file)))
                return False, None
        else:
            return status, data

    def get_config_template_data(self, serialnumber=None, templateName=None, groupName=None, isRaw=None):

        status, data = self.get_group_data(serialnumber=serialnumber, groupName=groupName)

        if status:

            grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=data)
            t_dir = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir
            t_file = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile

            if isRaw:

                try:
                    with open(t_dir + t_file) as tfile:
                        t_data = tfile.read()
                        return True, t_data

                except IOError as ioe:
                    return False, ioe.message
            else:

                try:
                    env = Environment(autoescape=False,
                                      loader=FileSystemLoader(t_dir), trim_blocks=True, lstrip_blocks=True)
                    self.logger.info(
                        Tools.create_log_msg(self.name, serialnumber, 'Found template <{0}>)'.format(t_file)))
                    return True, env.get_template(t_file)

                except (TemplateNotFound, IOError) as err:
                    self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                          'Error({0}): {1} --> {2})'.format(err.errno, err.strerror,
                                                                                            err.filename)))
                    return False, err
        else:
            return status, data

    def add_config_template_data(self, templateName=None, templateData=None, groupName=None):

        if groupName and templateName and templateData:

            isFile, grp_cfg = self.get_group_data(serialnumber=groupName, groupName=groupName)

            if isFile:

                grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)

                try:

                    with open(
                            grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir + templateName + c.CONFIG_FILE_SUFFIX_TEMPLATE,
                            'w') as fp:
                        fp.write(templateData)

                    return True, 'Successfully added template <{0}>'.format(templateName)

                except IOError as ioe:
                    return False, ioe.message

    def del_config_template_data(self, templateName=None, groupName=None):

        if groupName and templateName:

            isFile, grp_cfg = self.get_group_data(serialnumber=groupName, groupName=groupName)

            if isFile:

                grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)

                if os.path.exists(
                        grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir + templateName + c.CONFIG_FILE_SUFFIX_TEMPLATE):

                    os.remove(
                        grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir + templateName + c.CONFIG_FILE_SUFFIX_TEMPLATE)
                    return True, 'Successfully deleted template <{0}>'.format(templateName)

                else:
                    return False, 'File \<{0}\> not found'.format(templateName)

    def get_bootstrap_config_template(self, serialnumber=None, path=None, file=None):

        try:
            env = Environment(autoescape=False,
                              loader=FileSystemLoader(path),
                              trim_blocks=True, lstrip_blocks=True)
            self.logger.info("{0}-[{1}]: Found bootstrap template {2}".format(self.name, serialnumber, file))
            return True, env.get_template(file)

        except (TemplateNotFound, IOError) as err:
            self.logger.info("{0}-[{1}]: Error({2}): {3} --> {4})".format(self.name, serialnumber, err.errno,
                                                                          err.strerror, err.filename))
            return False, None

    def get_device_config_data_file(self, serialnumber=None, deviceOsshId=None):

        dev_conf_path = c.conf.STORAGE.Local.DeviceConfDataDir

        if serialnumber is not None:

            filename = serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE

            if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):
                self.logger.info(
                    Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))
                return True, dev_conf_path + filename

            else:
                self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                      logmsg.LOCAL_DEV_CFG_FILE_NOK.format(dev_conf_path + filename)))

                if deviceOsshId is not None:

                    filename = deviceOsshId + c.CONFIG_FILE_SUFFIX_DEVICE

                    if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):
                        self.logger.info(
                            Tools.create_log_msg(self.name, deviceOsshId,
                                                 logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))

                        return True, dev_conf_path + filename

                    else:
                        self.logger.info(
                            Tools.create_log_msg(self.name, deviceOsshId, logmsg.LOCAL_DEV_CFG_FILE_NOK.format(
                                dev_conf_path + filename)))
                        return False, None
                else:
                    self.logger.info(
                        Tools.create_log_msg(self.name, deviceOsshId, logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))
                    return False, None

        elif deviceOsshId is not None:

            filename = deviceOsshId + c.CONFIG_FILE_SUFFIX_DEVICE

            if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):
                self.logger.info(
                    Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))

                return True, dev_conf_path + filename

            else:
                self.logger.info(
                    Tools.create_log_msg(self.name, deviceOsshId, logmsg.LOCAL_DEV_CFG_FILE_NOK.format(filename)))
                return False, None
        else:
            self.logger.info(
                Tools.create_log_msg(self.name, serialnumber if serialnumber else deviceOsshId,
                                     logmsg.LOCAL_DEV_CFG_FILE_NOK.format(
                                         serialnumber if serialnumber else deviceOsshId)))
            return False, None

    def get_device_config_data(self, serialnumber=None, deviceOsshId=None, isRaw=None):

        dev_conf_path = c.conf.STORAGE.Local.DeviceConfDataDir

        if serialnumber is not None:

            filename = serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE

            if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):

                if isRaw:

                    try:
                        with open(c.conf.STORAGE.Local.DeviceConfDataDir + filename) as dfile:
                            d_data = dfile.read()
                            return True, d_data

                    except IOError as ioe:
                        return False, ioe.message

                else:

                    try:
                        with open(c.conf.STORAGE.Local.DeviceConfDataDir + filename, 'r') as fp:

                            try:

                                datavars = yaml.safe_load(fp)
                                self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                                      logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))

                                self.logger.info(
                                    Tools.create_log_msg(logmsg.CONF_VALIDATE,
                                                         serialnumber if serialnumber else deviceOsshId,
                                                         logmsg.CONF_VALIDATE_INIT.format('device')))
                                resp, err = self.validate(source=datavars,
                                                          lookup_type=c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG)

                                if resp:
                                    self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE,
                                                                          serialnumber if serialnumber else deviceOsshId,
                                                                          logmsg.CONF_VALIDATE_OK.format('Device')))
                                    return True, datavars
                                else:
                                    self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE,
                                                                          serialnumber if serialnumber else deviceOsshId,
                                                                          logmsg.CONF_VALIDATE_NOK.format(err)))
                                    return False, err

                            except yaml.YAMLError as exc:
                                self.logger.info(
                                    '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                                   serialnumber if serialnumber else deviceOsshId,
                                                                                                   dev_conf_path + filename,
                                                                                                   exc))
                                return False, '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                                             serialnumber if serialnumber else deviceOsshId,
                                                                                                             dev_conf_path + filename,
                                                                                                             exc)
                    except IOError:
                        self.logger.info('{0}-[{1}]: Error in opening config file <{2}>'.format(self.name,
                                                                                                serialnumber if serialnumber else deviceOsshId,
                                                                                                dev_conf_path + filename))
                        return False, '{0}-[{1}]: Error in opening config file <{2}>'.format(self.name,
                                                                                             serialnumber if serialnumber else deviceOsshId,
                                                                                             dev_conf_path + filename)
            else:

                if deviceOsshId is not None:

                    filename = deviceOsshId + c.CONFIG_FILE_SUFFIX_DEVICE

                    if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):

                        try:
                            with open(c.conf.STORAGE.Local.DeviceConfDataDir + filename, 'r') as fp:

                                try:

                                    datavars = yaml.safe_load(fp)
                                    self.logger.info(Tools.create_log_msg(self.name, deviceOsshId,
                                                                          logmsg.LOCAL_DEV_CFG_FILE_OK.format(
                                                                              filename)))

                                    return True, datavars

                                except yaml.YAMLError as exc:
                                    self.logger.info(
                                        '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                                       deviceOsshId,
                                                                                                       dev_conf_path + filename,
                                                                                                       exc))
                                    return False, None

                        except IOError:
                            self.logger.info(
                                '{0}-[{1}]: Error in opening config file <{2}>'.format(self.name, deviceOsshId,
                                                                                       dev_conf_path + filename))
                            return False, None

                    else:
                        self.logger.info(Tools.create_log_msg(self.name, deviceOsshId,
                                                              logmsg.LOCAL_DEV_CFG_FILE_NOK.format(
                                                                  dev_conf_path + filename)))
                        return False, None

                else:
                    self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                          logmsg.LOCAL_DEV_CFG_FILE_NOK.format(
                                                              dev_conf_path + filename)))
                    return False, None

        elif deviceOsshId is not None:

            filename = deviceOsshId + c.CONFIG_FILE_SUFFIX_DEVICE

            if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):

                try:
                    with open(c.conf.STORAGE.Local.DeviceConfDataDir + filename, 'r') as fp:

                        try:

                            datavars = yaml.safe_load(fp)
                            self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                                  logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))
                            return True, datavars

                        except yaml.YAMLError as exc:
                            self.logger.info(
                                '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                               deviceOsshId,
                                                                                               dev_conf_path + filename,
                                                                                               exc))
                            return False, None

                except IOError:
                    self.logger.info('{0}-[{1}]: Error in reading config file <{2}>'.format(self.name, deviceOsshId,
                                                                                            dev_conf_path + filename))
                    return False, None

            else:
                self.logger.info(Tools.create_log_msg(self.name, deviceOsshId,
                                                      logmsg.LOCAL_DEV_CFG_FILE_NOK.format(
                                                          dev_conf_path + filename)))
                return False, None

        else:
            self.logger.info(Tools.create_log_msg(self.name, None, 'Missing device serial and ossh id'))
            return False, None

    def add_device_config_data(self, configSerial=None, configData=None):

        if configSerial and configData:

            try:

                with open(c.conf.STORAGE.Local.DeviceConfDataDir + configSerial + c.CONFIG_FILE_SUFFIX_DEVICE,
                          'w') as fp:
                    fp.write(configData)

                return True, logmsg.LOCAL_GRP_CFG_FILE_ADD_OK.format(configSerial)

            except IOError as ioe:
                return False, ioe

    def del_device_config_data(self, configSerial=None):

        if os.path.exists(c.conf.STORAGE.Local.DeviceConfDataDir + configSerial + c.CONFIG_FILE_SUFFIX_DEVICE):

            os.remove(c.conf.STORAGE.Local.DeviceConfDataDir + configSerial + c.CONFIG_FILE_SUFFIX_DEVICE)
            return True, logmsg.LOCAL_GRP_CFG_FILE_DEL_OK.format(configSerial)

        else:
            return False, 'File \<{0}\> not found'.format(configSerial)

    def get_group_data_file(self, serialnumber=None, group=None, isRaw=None):

        group_file_path = c.conf.STORAGE.Local.DeviceGrpFilesDir
        filename = group + c.CONFIG_FILE_SUFFIX_GROUP

        if os.path.exists(group_file_path + filename) and os.path.isfile(group_file_path + filename):

            try:
                with open(group_file_path + filename, 'r') as fp:
                    datavars = yaml.safe_load(fp)
                    self.logger.info(
                        Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))
                    return True, datavars

            except IOError:
                self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                      logmsg.LOCAL_GRP_CFG_FILE_NOK.format(serialnumber,
                                                                                           group_file_path + filename)))
                return False, None

        else:
            self.logger.info(
                Tools.create_log_msg(self.name, serialnumber,
                                     logmsg.LOCAL_GRP_CFG_FILE_MISS.format(group_file_path + filename)))
            return False, None

    def get_group_data(self, serialnumber=None, groupName=None, isRaw=None):

        filename = groupName + c.CONFIG_FILE_SUFFIX_GROUP

        if isRaw:

            try:
                with open(c.conf.STORAGE.Local.DeviceGrpFilesDir + filename) as gfile:
                    g_data = gfile.read()
                    return True, g_data

            except IOError as ioe:
                return False, ioe
        else:

            try:

                with open(c.conf.STORAGE.Local.DeviceGrpFilesDir + filename, 'r') as fp:

                    try:
                        datavars = yaml.safe_load(fp.read())

                        self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                              logmsg.LOCAL_GRP_CFG_FILE_OK.format(filename)))

                        self.logger.info(
                            Tools.create_log_msg(logmsg.CONF_VALIDATE, serialnumber,
                                                 logmsg.CONF_VALIDATE_INIT.format('group')))
                        resp, err = self.validate(source=datavars,
                                                  lookup_type=c.CONFIG_LOOKUP_TYPE_GET_GROUP)

                        if resp:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, serialnumber,
                                                                  logmsg.CONF_VALIDATE_OK.format('Group')))
                            return True, datavars
                        else:
                            self.logger.info(Tools.create_log_msg(logmsg.CONF_VALIDATE, serialnumber,
                                                                  logmsg.CONF_VALIDATE_NOK.format(err)))
                            return False, err

                    except yaml.YAMLError as exc:
                        c.logger.info(
                            Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_GRP_CFG_FILE_NOK(filename, exc.message)))
                        return False, Tools.create_log_msg(self.name, serialnumber,
                                                           logmsg.LOCAL_GRP_CFG_FILE_NOK.format(filename, exc.message))

            except IOError as ioe:
                c.logger.info(Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_GRP_CFG_FILE_MISS.format(filename)))
                return False, ioe

    def add_group_data(self, groupName=None, groupData=None):

        if groupName and groupData:

            try:

                with open(c.conf.STORAGE.Local.DeviceGrpFilesDir + groupName + c.CONFIG_FILE_SUFFIX_GROUP,
                          'w') as fp:
                    fp.write(groupData)

                return True, logmsg.LOCAL_GRP_CFG_FILE_ADD_OK.format(groupName)

            except Exception as e:
                return False, e.message

    def del_group_data(self, groupName=None):

        if os.path.exists(c.conf.STORAGE.Local.DeviceGrpFilesDir + groupName + c.CONFIG_FILE_SUFFIX_GROUP):

            os.remove(c.conf.STORAGE.Local.DeviceGrpFilesDir + groupName + c.CONFIG_FILE_SUFFIX_GROUP)
            return True, logmsg.LOCAL_GRP_CFG_FILE_DEL_OK.format(groupName)

        else:
            return False, 'File \<{0}\> not found'.format(groupName)
