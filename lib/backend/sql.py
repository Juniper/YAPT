# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import datetime

from peewee import BooleanField
from peewee import CharField
from peewee import DateTimeField
from peewee import DoesNotExist
from peewee import Field
from peewee import FloatField
from peewee import ForeignKeyField
from peewee import IntegerField
from peewee import IntegrityError
from peewee import Model
from peewee import SqliteDatabase
from peewee import TextField
from peewee import prefetch

from lib.amqp.amqpmessage import AMQPMessage
from lib.backend.backend import Backend
import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogSqlBackend as logmsg
from lib.sampledevice import SampleDevice
from lib.tools import Tools

tools = Tools()
database = SqliteDatabase(c.conf.BACKEND.Sqlite.DbPath + c.conf.BACKEND.Sqlite.DbName, threadlocals=True,
                          fields={'provtaskseq': 'provtaskseq'})


class Sql(Backend):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(Sql, self).__init__(group, target, name, args, kwargs, verbose)
        self._logger.debug(
            Tools.create_log_msg(self.__class__.__name__, None,
                                 LogCommon.IS_SUBCLASS.format(self.__class__.__name__, issubclass(Sql, Backend))))
        self._logger.info(Tools.create_log_msg(logmsg.SQLBACKEND, None, logmsg.SQLBACKEND_STARTED))
        self.DeviceTasks = None

        if c.conf.BACKEND.Sqlite.AutoCreateDb:
            task_plugins = Tools.get_task_plugins()
            self.DeviceTasks = Sql.create_tables(dbname='devicetasks', fields=task_plugins, refName='Tasks')
        else:
            pass

    @classmethod
    def create_tables(cls, dbname=None, fields=None, refName=None):
        dynTable = taskFactory(dbName=dbname, fields=fields, refName=refName)
        tables = [Device, dynTable, Site, Asset, Group, Template, Image, Service, DeviceConfig]
        database.connect()
        database.create_tables(tables, safe=True)
        database.close()

        return dynTable

    def add_device(self, new_device):

        device, created = Device.get_or_create(
            deviceSerial=new_device.deviceSerial,
            defaults={'deviceName': new_device.deviceName, 'deviceModel': new_device.deviceModel,
                      'deviceSerial': new_device.deviceSerial, 'softwareVersion': new_device.softwareVersion,
                      'deviceIP': new_device.deviceIP, 'deviceStatus': c.DEVICE_STATUS_NEW,
                      'deviceTimeStamp': new_device.deviceTimeStamp,
                      'deviceConfiguration': new_device.deviceConfiguration,
                      'deviceConnection': new_device.deviceConnection,
                      'deviceGroup': new_device.deviceGroup,
                      'deviceSourcePlugin': new_device.deviceSourcePlugin,
                      'deviceTaskSeq': new_device.deviceTaskSeq, })

        if created:

            dpts = self.DeviceTasks.create(owner=new_device.deviceSerial)
            dpts.save()
            database.close()
            new_device.deviceStatus = c.DEVICE_STATUS_NEW

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_ADD,
                                  payload=new_device, source=c.AMQP_PROCESSOR_BACKEND)
            self.amqpCl.send_message(message=message)

            return new_device

        else:
            new_device.deviceStatus = c.DEVICE_STATUS_EXISTS
            device.deviceName = new_device.deviceName
            device.deviceIP = new_device.deviceIP
            device.deviceStatus = new_device.deviceStatus
            device.softwareVersion = new_device.softwareVersion
            device.deviceTimeStamp = new_device.deviceTimeStamp
            device.deviceConfiguration = new_device.deviceConfiguration
            device.deviceConnection = new_device.deviceConnection
            device.deviceGroup = new_device.deviceGroup
            device.deviceSourcePlugin = new_device.deviceSourcePlugin
            device.deviceTaskSeq = new_device.deviceTaskSeq
            device.deviceTaskProgress = 0.0
            device.save()

            new_device.deviceTasks.deviceSerial = new_device.deviceSerial
            new_device.deviceTasks.is_callback = False

            for item in device.deviceTaskSeq:
                new_device.deviceTasks.taskState[item] = {'taskState': c.TASK_STATE_WAIT,
                                                          'taskStateMsg': c.TASK_STATE_MSG_WAIT}
                key = {item: c.TASK_STATE_MSG_WAIT}
                query = self.DeviceTasks.update(**key). \
                    where(self.DeviceTasks.owner == new_device.deviceSerial)
                query.execute()

            new_device.deviceTasks.is_callback = True
            database.close()

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_UI_UPDATE_AND_RESET, payload=new_device,
                                  source=c.AMQP_PROCESSOR_BACKEND)
            self.amqpCl.send_message(message=message)

            return new_device

    def add_device_config(self, configSerial=None, configDescr=None, configConfigSource=None):

        try:
            DeviceConfig.create(configSerial=configSerial, configDescr=configDescr,
                                configConfigSource=configConfigSource)
            database.close()
            return True, "Successfully added new device configuration <{0}>".format(configSerial)

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', configSerial, ie.message)
            return False, "Failed to add new device configuration <{0}> with error <{1}>".format(configSerial,
                                                                                                 ie.message)

    def del_device_config(self, configSerial=None):

        try:

            config = DeviceConfig.get(DeviceConfig.configSerial == configSerial)
            config.delete_instance()
            return True, "Successfully deleted device config <{0}>".format(configSerial)

        except DoesNotExist as dne:
            return False, dne.message

    def get_device_config_by_sn(self, configSerial=None):

        try:
            devcfg = DeviceConfig.get(DeviceConfig.configSerial == configSerial)

            return True, {'configId': devcfg.configId, 'configSerial': devcfg.configSerial, 'configDescr': devcfg.configDescr,
                          'configConfigSource': devcfg.configConfigSource}

        except DoesNotExist as dne:
            return False, dne.message

    def get_device_configs(self):

        configs = list()

        try:
            query = prefetch(DeviceConfig.select())

            for config in query:
                configData = {'configId': config.configId, 'configSerial': config.configSerial,
                              'configDescr': config.configDescr, 'configConfigSource': config.configConfigSource}
                configs.append(configData)

            return True, configs

        except DoesNotExist as dne:
            return False, dne.message

    def update_device(self, sample_device):

        query = Device.update(deviceName=sample_device.deviceName, deviceModel=sample_device.deviceModel,
                              deviceSerial=sample_device.deviceSerial, softwareVersion=sample_device.softwareVersion,
                              deviceIP=sample_device.deviceIP,
                              deviceStatus=sample_device.deviceStatus,
                              deviceTaskProgress=sample_device.deviceTaskProgress,
                              deviceConfiguration=sample_device.deviceConfiguration,
                              deviceIsRebooted=sample_device.deviceIsRebooted,
                              deviceConnection=sample_device.deviceConnection,
                              deviceGroup=sample_device.deviceGroup,
                              deviceSourcePlugin=sample_device.deviceSourcePlugin,
                              deviceTaskSeq=sample_device.deviceTaskSeq).where(
            Device.deviceSerial == sample_device.deviceSerial)

        query.execute()

        device = Device.get(Device.deviceSerial == sample_device.deviceSerial)
        sample_device.deviceName = device.deviceName
        sample_device.deviceIP = device.deviceIP
        sample_device.deviceSerial = device.deviceSerial
        sample_device.deviceModel = device.deviceModel
        sample_device.deviceStatus = device.deviceStatus
        sample_device.softwareVersion = device.softwareVersion
        sample_device.deviceTaskProgress = device.deviceTaskProgress
        sample_device.deviceConfiguration = device.deviceConfiguration
        sample_device.deviceConnection = device.deviceConnection
        sample_device.deviceGroup = device.deviceGroup
        sample_device.deviceSourcePlugin = device.deviceSourcePlugin
        sample_device.deviceTaskSeq = device.deviceTaskSeq

        database.close()

        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE,
                              payload=sample_device, source=c.AMQP_PROCESSOR_BACKEND)

        self.amqpCl.send_message(message=message)

        return sample_device

    def update_device_task_state(self, device_serial, is_callback, task_name, task_state):

        key = {task_name: task_state['taskStateMsg']}
        query = self.DeviceTasks.update(**key). \
            where(self.DeviceTasks.owner == device_serial)
        query.execute()
        database.close()
        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE_TASK_STATE,
                              payload=[device_serial, task_name, task_state],
                              source=c.AMQP_PROCESSOR_BACKEND)

        self.amqpCl.send_message(message=message)

    def get_device(self, serial_number):

        try:
            return Device.get(Device.deviceSerial == serial_number)
        except DoesNotExist:
            return False

    def get_devices(self):

        sample_devices = dict()

        for device in Device.select():

            sample_device = SampleDevice(deviceIP=device.deviceIP, deviceStatus=device.deviceStatus,
                                         deviceTimeStamp=device.deviceTimeStamp.strftime("%Y-%m-%d %H:%M:%S"),
                                         deviceSourcePlugin=device.deviceSourcePlugin)
            sample_device.deviceSerial = device.deviceSerial
            sample_device.deviceName = device.deviceName
            sample_device.deviceModel = device.deviceModel
            sample_device.deviceConfiguration = device.deviceConfiguration
            sample_device.deviceIsRebooted = device.deviceIsRebooted
            sample_device.softwareVersion = device.softwareVersion
            sample_device.deviceTaskProgress = device.deviceTaskProgress
            sample_device.deviceGroup = device.deviceGroup
            sample_device.deviceConnection = device.deviceConnection
            sample_device.deviceTaskSeq = device.deviceTaskSeq
            sample_device.is_callback = True
            sample_devices[device.deviceSerial] = dict()
            sample_devices[device.deviceSerial]['data'] = sample_device

            task = self.DeviceTasks.get(device.deviceSerial == self.DeviceTasks.owner)
            sample_device.deviceTasks.deviceSerial = sample_device.deviceSerial

            sample_device.deviceTasks.is_callback = False

            for item in sample_device.deviceTaskSeq:
                sample_device.deviceTasks.taskState[item] = task._data[item]

            sample_device.deviceTasks.is_callback = True

        database.close()

        return sample_devices

    def add_site(self, siteId=None, siteName=None, siteDescr=None):

        try:
            Site.create(siteId=siteId, siteName=siteName, siteDescr=siteDescr)
            database.close()
            return True, "Successfully added site <{0}>".format(siteId)

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', siteId, ie)
            return False, ie.message

    def del_site(self, siteId=None):

        try:

            site = Site.get(Site.siteId == siteId)
            site.delete_instance(recursive=True)
            return True, "Successfully deleted site <{0}>".format(siteId)

        except DoesNotExist as dne:
            return False, dne.message

    def add_asset_to_site(self, assetSiteId=None, assetSerial=None, assetConfigId=None, assetDescr=None):

        try:

            Asset.create(assetSiteId=assetSiteId, assetSerial=assetSerial, assetConfigId=assetConfigId,
                         assetDescr=assetDescr)
            database.close()
            return True, "Successfully assigned asset <{0}> to site <{1}>".format(assetConfigId, assetSiteId)

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', assetConfigId, ie)
            return False, ie.message

    def get_site_by_id(self, siteId=None):
        siteData = dict()

        try:
            query = prefetch(Site.select().where(Site.siteId == siteId), Asset)

            for site in query:
                siteData = {'siteId': site.siteId, 'siteName': site.siteName, 'siteDescr': site.siteDescr}
                assets = list()

                for asset in site.refSite_prefetch:
                    assetData = {'assetSerial': asset.assetSerial, 'assetConfigId': asset.assetConfigId,
                                 'assetDescr': asset.assetDescr}
                    assets.append(assetData)

                siteData['assets'] = assets

            return True, siteData

        except DoesNotExist as dne:
            return False, dne.message

    def get_sites(self):
        sites = list()

        try:
            query = prefetch(Site.select(), Asset)

            for site in query:

                siteData = {'siteId': site.siteId, 'siteName': site.siteName, 'siteDescr': site.siteDescr}
                assets = list()

                for asset in site.refSite_prefetch:
                    assetData = {'assetSerial': asset.assetSerial, 'assetConfigId': asset.assetConfigId,
                                 'assetDescr': asset.assetDescr}
                    assets.append(assetData)

                siteData['assets'] = assets
                sites.append(siteData)

            return True, sites

        except DoesNotExist as dne:
            return False, dne.message

    def get_asset_by_site_id(self, assetSiteId=None):
        assets = list()

        try:
            data = Asset.select().where(Asset.assetSiteId == assetSiteId)

            for asset in data:
                assetData = {'assetId': asset.assetId, 'assetSiteId': asset.assetSiteId.siteId,
                             'assetSerial': asset.assetSerial, 'assetConfigId': asset.assetConfigId,
                             'assetDescr': asset.assetDescr}
                assets.append(assetData)

            return True, assets

        except DoesNotExist as dne:
            return False, dne.message

    def get_asset_by_serial(self, assetSerial=None):

        try:
            data = Asset.get(Asset.assetSerial == assetSerial).assetConfigId
            return True, data

        except DoesNotExist as dne:
            return False, dne.message

    def update_asset_site_mapping(self, assetSiteId=None, assetSerial=None, assetConfigId=None):

        query = Asset.update(assetSerial=assetSerial).where(Asset.assetConfigId == assetConfigId)
        query.execute()
        database.close()

        return True

    def add_group(self, groupName=None, groupConfig=None, groupDescr=None, groupConfigSource=None):

        try:
            Group.create(groupName=groupName, groupDescr=groupDescr, groupConfigSource=groupConfigSource)
            database.close()
            return True, "Successfully added new group <{0}>".format(groupName)

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', groupName, ie.message)
            return False, "Failed to add new group <{0}> with error <{1}>".format(groupName, ie.message)

    def del_group_by_name(self, groupName=None):

        try:

            group = Group.get(Group.groupName == groupName)
            group.delete_instance()
            return True, "Successfully deleted group <{0}>".format(groupName)

        except DoesNotExist as dne:
            return False, dne.message

    def get_group_by_name(self, groupName=None):

        try:
            group = Group.get(Group.groupName == groupName)

            return True, {'groupId': group.groupId, 'groupName': group.groupName, 'groupDescr': group.groupDescr,
                          'groupConfigSource': group.groupConfigSource}

        except DoesNotExist as dne:
            return False, dne.message

    def get_groups(self):

        groups = list()

        try:
            query = prefetch(Group.select())

            for group in query:
                groupData = {'groupId': group.groupId, 'groupName': group.groupName, 'groupDescr': group.groupDescr,
                             'groupConfigSource': group.groupConfigSource}
                groups.append(groupData)

            return True, groups

        except DoesNotExist as dne:
            return False, dne.message

    def add_template(self, templateName=None, templateConfig=None, templateDescr=None, templateConfigSource=None,
                     templateDevGrp=None):

        try:
            Template.create(templateName=templateName, templateDescr=templateDescr,
                            templateConfigSource=templateConfigSource, templateDevGrp=templateDevGrp)
            database.close()
            return True, "Successfully added new template <{0}>".format(templateName)

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', templateName, ie.message)
            return False, "Failed to add new template <{0}> with error <{1}>".format(templateName, ie.message)

    def del_template_by_name(self, templateName=None):

        try:

            template = Template.get(Template.templateName == templateName)
            template.delete_instance()
            return True, "Successfully deleted template <{0}>".format(templateName)

        except DoesNotExist as dne:
            return False, dne.message

    def get_template_by_name(self, templateName=None):

        try:
            template = Template.get(Template.templateName == templateName)
            return True, {'templateId': template.templateId, 'templateName': template.templateName,
                          'templateDescr': template.templateDescr,
                          'templateDevGrp': template.templateDevGrp,
                          'templateConfigSource': template.templateConfigSource}

        except DoesNotExist as dne:
            return False, dne.message

    def get_templates(self):

        templates = list()

        try:
            query = prefetch(Template.select())

            for template in query:
                templateData = {'templateId': template.templateId, 'templateName': template.templateName,
                                'templateDescr': template.templateDescr, 'templateConfigSource': template.templateConfigSource }
                templates.append(templateData)

            return True, templates

        except DoesNotExist as dne:
            return False, dne.message

    def add_image(self, imageName=None, imageDescr=None):

        try:
            Image.create(imageName=imageName, imageDescr=imageDescr)
            database.close()
            return True, "Successfully added new image <{0}>".format(imageName)

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', imageName, ie.message)
            return False, "Failed to add new image <{0}> with error <{1}>".format(imageName, ie.message)

    def del_image_by_name(self, imageName=None):

        try:

            image = Image.get(Image.imageName == imageName)
            image.delete_instance()
            return True, "Successfully deleted image <{0}>".format(imageName)

        except DoesNotExist as dne:
            return False, dne.message

    def get_image_by_name(self, imageName=None):

        try:
            image = Image.get(Image.imageName == imageName)
            return True, image

        except DoesNotExist as dne:
            return False, dne.message

    def get_images(self):

        images = list()

        try:
            query = prefetch(Image.select())

            for image in query:
                imageData = {'imageId': image.imageId, 'imageName': image.imageName,
                             'imageDescr': image.imageDescr}
                images.append(imageData)

            return True, images

        except DoesNotExist as dne:
            return False, dne.message

    def get_service_by_name(self, serviceName=None):
        pass

    def get_services(self):

        services = list()

        try:
            query = prefetch(Service.select())

            for service in query:
                serviceData = {'serviceName': service.serviceName, 'serviceDescr': service.serviceDescr,
                               'serviceStatus': service.serviceStatus}
                services.append(serviceData)

            return True, services

        except DoesNotExist as dne:
            return False, dne.message


class DeviceTaskSeqField(Field):
    db_field = 'taskseq'

    def db_value(self, value):
        return str(value)

    def python_value(self, value):
        # Value (Unicode) contains literals which we don't want to be displayed.
        # There should be a better way doing this
        value = value.replace("[", "")
        value = value.replace("]", "")
        value = value.replace("u'", "")
        value = value.replace("'", "")
        value = value.replace(" ", "")
        return value.split(',')


class BaseModel(Model):
    class Meta:
        database = database


class Device(BaseModel):
    deviceName = CharField(default='init')
    deviceModel = CharField(default='')
    deviceSerial = CharField(unique=True, primary_key=True)
    softwareVersion = CharField(default='')
    deviceIP = CharField(default='')
    deviceTimeStamp = DateTimeField(default=datetime.datetime.now)
    deviceConnection = CharField(default='')
    deviceIsRebooted = BooleanField(default=False)
    deviceConfiguration = TextField(default='')
    deviceStatus = CharField(default='')
    deviceTaskProgress = FloatField(default=0.0)
    deviceGroup = CharField(default='')
    deviceSourcePlugin = CharField(default='')
    deviceTaskSeq = DeviceTaskSeqField(default='')
    deviceTasks = dict()


class DeviceConfig(BaseModel):
    configId = IntegerField(unique=True, primary_key=True)
    configSerial = CharField(unique=True, null=False)
    configDescr = CharField(default='new device config')
    configConfigSource = CharField(default='local')


class Site(BaseModel):
    siteId = CharField(unique=True, primary_key=True)
    siteName = CharField(unique=True, null=False)
    siteDescr = CharField(default='')


class Asset(BaseModel):
    assetId = IntegerField(unique=True, primary_key=True)
    assetSiteId = ForeignKeyField(Site, related_name='refSite')
    # assetSerial should be unique. How to initialize unique key with empty value? Does this make sense Unique key empty value?
    assetSerial = CharField(null=True)
    assetConfigId = CharField(unique=True, null=False)
    assetDescr = CharField(default='')


class Group(BaseModel):
    groupId = IntegerField(unique=True, primary_key=True)
    groupName = CharField(unique=True, null=False)
    groupDescr = CharField(default='New group')
    groupConfigSource = CharField(default='local')


# Template should be part of group?
class Template(BaseModel):
    templateId = IntegerField(unique=True, primary_key=True)
    templateName = CharField(unique=True, null=False)
    templateDescr = CharField(default='New template')
    templateDevGrp = CharField(default='mygroup')
    templateConfigSource = CharField(default='local')


class Image(BaseModel):
    imageId = IntegerField(unique=True, primary_key=True)
    imageName = CharField(unique=True, null=False)
    imageDescr = CharField(default='New image')


class Service(BaseModel):
    serviceId = IntegerField(unique=True, primary_key=True)
    serviceName = CharField(unique=True, null=False)
    serviceDescr = CharField(default='New service')
    serviceStatus = CharField(default='stopped')


def taskFactory(dbName=None, fields=None, refName=None):
    class DynamicTable(BaseModel):
        owner = ForeignKeyField(Device, related_name=refName, unique=True, primary_key=True)

        class Meta:
            validate_backrefs = False
            db_table = dbName

    for field in fields:
        CharField(default='Waiting').add_to_class(DynamicTable, field)
    return DynamicTable
