# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#

import os

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from lib.config.source import DeviceConfigSource
import lib.constants as c
from lib.logmsg import LogLocal as logmsg
from lib.tools import Tools


class Local(DeviceConfigSource):

    def __init__(self):
        super(Local, self).__init__()

    def get_config_template_file(self, serialnumber=None, grp_cfg=None):

        template_file_path = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir
        filename = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile

        if os.path.exists(template_file_path + filename) and os.path.isfile(template_file_path + filename):
            self.logger.info(Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_TEMPLATE_FILE_OK.format(
                template_file_path + filename)))
            return True, template_file_path + filename

        else:
            self.logger.info(Tools.create_log_msg(self.name, serialnumber, logmsg.LOCAL_TEMPLATE_FILE_NOK.format(
                template_file_path + filename)))
            return False, None

    def get_config_template_data(self, serialnumber=None, grp_cfg=None):

        try:
            env = Environment(autoescape=False,
                              loader=FileSystemLoader(grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir),
                              trim_blocks=True, lstrip_blocks=True)
            self.logger.info(Tools.create_log_msg(self.name, serialnumber, 'Found template <{0}>)'.format(
                grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile)))
            return True, env.get_template(grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile)

        except (TemplateNotFound, IOError) as err:
            self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                  'Error({0}): {1} --> {2})'.format(err.errno, err.strerror,
                                                                                    err.filename)))
            return False, err

    def add_config_template_data(self, templateName=None, templateData=None, group=None):

        if group and templateName and templateData:

            isFile, grp_cfg = self.get_group_data(serialnumber=group, group=group)

            if isFile:

                grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)

                try:

                    with open(grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir + templateName + '.j2',
                              'w') as fp:
                        fp.write(templateData)

                    return True, 'Successfully added template <{0}>'.format(templateName)

                except Exception as e:
                    return False, e.message

    def del_config_template_data(self, templateName=None, group=None):

        if group and templateName:

            isFile, grp_cfg = self.get_group_data(serialnumber=group, group=group)

            if isFile:

                grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=grp_cfg)

                if os.path.exists(grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir + templateName + '.j2'):

                    os.remove(grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateDir + templateName + '.j2')
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

    def get_config_data_file(self, serialnumber=None, deviceOsshId=None):

        dev_conf_path = c.conf.SOURCE.Local.DeviceConfDataDir

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

    def get_config_data(self, serialnumber=None, deviceOsshId=None):

        dev_conf_path = c.conf.SOURCE.Local.DeviceConfDataDir

        if serialnumber is not None:

            filename = serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE

            if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):

                try:
                    with open(c.conf.SOURCE.Local.DeviceConfDataDir + filename, 'r') as fp:

                        try:

                            datavars = yaml.safe_load(fp)
                            self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                                  logmsg.LOCAL_DEV_CFG_FILE_OK.format(filename)))

                            return True, datavars

                        except yaml.YAMLError as exc:
                            self.logger.info(
                                '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                               serialnumber if serialnumber else deviceOsshId,
                                                                                               dev_conf_path + filename,
                                                                                               exc))
                            return False, None

                except IOError:
                    self.logger.info('{0}-[{1}]: Error in opening config file <{2}>'.format(self.name,
                                                                                            serialnumber if serialnumber else deviceOsshId,
                                                                                            dev_conf_path + filename))
                    return False, None
            else:

                if deviceOsshId is not None:

                    filename = deviceOsshId + c.CONFIG_FILE_SUFFIX_DEVICE

                    if os.path.exists(dev_conf_path + filename) and os.path.isfile(dev_conf_path + filename):

                        try:
                            with open(c.conf.SOURCE.Local.DeviceConfDataDir + filename, 'r') as fp:

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
                    with open(c.conf.SOURCE.Local.DeviceConfDataDir + filename, 'r') as fp:

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

    def get_group_data_file(self, serialnumber=None, group=None):

        group_file_path = c.conf.SOURCE.Local.DeviceGrpFilesDir
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

    def get_group_data(self, serialnumber=None, group=None):

        filename = group + c.CONFIG_FILE_SUFFIX_GROUP

        try:

            return True, yaml.safe_load(open(c.conf.SOURCE.Local.DeviceGrpFilesDir + filename).read())

        except IOError as ioe:
            c.logger.info(
                Tools.create_log_msg(self.name, serialnumber, logmsg.__format__(filename, ioe.message)))
            return False, None

    def add_group_data(self, groupName=None, groupData=None):

        if groupName and groupData:

            try:

                with open(c.conf.SOURCE.Local.DeviceGrpFilesDir + groupName + c.CONFIG_FILE_SUFFIX_GROUP,
                          'w') as fp:
                    fp.write(groupData)

                return True, logmsg.LOCAL_GRP_CFG_FILE_ADD_OK.format(groupName)

            except Exception as e:
                return False, e.message

    def del_group_data(self, groupName=None):

        if os.path.exists(c.conf.SOURCE.Local.DeviceGrpFilesDir + groupName + c.CONFIG_FILE_SUFFIX_GROUP):

            os.remove(c.conf.SOURCE.Local.DeviceGrpFilesDir + groupName + c.CONFIG_FILE_SUFFIX_GROUP)
            return True, logmsg.LOCAL_GRP_CFG_FILE_DEL_OK.format(groupName)

        else:
            return False, 'File \<{0}\> not found'.format(groupName)
