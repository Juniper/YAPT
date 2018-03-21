# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#

import abc
import yaml
from lib.logmsg import LogConfigSource as logmsg
import lib.constants as c
from lib.tools import Tools
from cerberus import Validator


class DeviceConfigSource(object):
    def __init__(self):
        self.logger = c.logger
        self.name = self.__class__.__name__.upper()

    @abc.abstractmethod
    def get_config_template_file(self, serialnumber, grp_cfg):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_config_template_data(self, serialnumber, grp_cfg):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_config_template_data(self, templateName, templateData, group):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_config_template_data(self, templateName, group):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_bootstrap_config_template(self, serialnumber, path, file):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_config_data_file(self, serialnumber, deviceOsshId):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_config_data(self, serialnumber, deviceOsshId):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_group_data_file(self, serialnumber, group):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_group_data(self, serialnumber, group):
        raise NotImplementedError()

    @abc.abstractmethod
    def add_group_data(self, groupName, groupData):
        raise NotImplementedError()

    @abc.abstractmethod
    def del_group_data(self, groupName):
        raise NotImplementedError()

    def validate(self, source=None, lookup_type=None):

        if lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_DEVICE:

            if 'device_type' in source['yapt']:
                with open('conf/schema/device/' + source['yapt']['device_type'].lower() + c.CONFIG_FILE_SUFFIX_DEVICE, 'r') as stream:
                    schema = yaml.safe_load(stream)

                v = Validator()
                v.allow_unknown = True
                return v.validate(document=source, schema=schema), v.errors
            else:
                Tools.create_log_msg(self.name, None, logmsg.SOURCE_DEV_TYPE_NOK.format(hex(id(source))))
                return False, None

        elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_DEVICE_FILE:

            with open(source, 'r') as stream:
                doc = yaml.safe_load(stream)

            if 'device_type' in doc['yapt']:

                with open('conf/schema/device/' + doc['yapt']['device_type'].lower() + c.CONFIG_FILE_SUFFIX_DEVICE, 'r') as stream:
                    schema = yaml.safe_load(stream)

                v = Validator()
                v.allow_unknown = True
                return v.validate(document=doc, schema=schema), v.errors

            else:
                Tools.create_log_msg(self.name, None, logmsg.SOURCE_DEV_TYPE_NOK.format(hex(id(source))))
                return False, None

        elif lookup_type == c.CONFIG_SOURCE_LOOKUP_TYPE_GET_GROUP or c.CONFIG_SOURCE_LOOKUP_TYPE_GET_GROUP:

            with open('conf/schema/group/group.yml', 'r') as stream:
                schema = yaml.safe_load(stream)

            v = Validator()
            v.allow_unknown = True
            return v.validate(document=source, schema=schema), v.errors
