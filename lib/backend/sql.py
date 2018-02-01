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
        database.connect()
        database.create_tables([Device, dynTable, Site, Asset, Group], safe=True)
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

            if new_device.is_callback:
                new_device.is_callback = False

            for item in device.deviceTaskSeq:
                new_device.deviceTasks.taskState[item] = {'taskState': c.TASK_STATE_WAIT,
                                                          'taskStateMsg': c.TASK_STATE_MSG_WAIT}
                key = {item: c.TASK_STATE_MSG_WAIT}
                query = self.DeviceTasks.update(**key). \
                    where(self.DeviceTasks.owner == new_device.deviceSerial)
                query.execute()

            new_device.is_callback = True
            database.close()

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_UI_UPDATE_AND_RESET, payload=new_device,
                                  source=c.AMQP_PROCESSOR_BACKEND)
            self.amqpCl.send_message(message=message)

            return new_device

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

    def update_device_task_state(self, sample_device, task_name, task_state, task_state_msg):

        if sample_device.is_callback:
            sample_device.is_callback = False

        key = {task_name: task_state_msg}
        query = self.DeviceTasks.update(**key). \
            where(self.DeviceTasks.owner == sample_device.deviceSerial)
        query.execute()

        query = Device.update(deviceStatus=sample_device.deviceStatus,
                              deviceTaskProgress=sample_device.deviceTaskProgress, ). \
            where(Device.deviceSerial == sample_device.deviceSerial)

        query.execute()
        database.close()

        sample_device.is_callback = True
        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE_TASK_STATE,
                              payload=[sample_device, task_name],
                              source=c.AMQP_PROCESSOR_BACKEND)

        self.amqpCl.send_message(message=message)

        return sample_device

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

            if sample_device.is_callback:
                sample_device.is_callback = False

            for item in sample_device.deviceTaskSeq:
                sample_device.deviceTasks.taskState[item] = task._data[item]

            sample_device.is_callback = True

        database.close()

        return sample_devices

    def add_site(self, siteId=None, siteName=None, siteDescr=None):

        try:
            new_site = Site.create(siteId=siteId, siteName=siteName, siteDescr=siteDescr)
            new_site.save()
            database.close()
            return True

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', siteId, ie)
            return False

    def add_asset_to_site(self, assetSiteId=None, assetSerial=None, assetConfigId=None, assetDescr=None):

        try:

            Asset.create(assetSiteId=assetSiteId, assetSerial=assetSerial, assetConfigId=assetConfigId,
                         assetDescr=assetDescr)
            database.close()
            return True

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', assetConfigId, ie)
            return False

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

            return siteData

        except DoesNotExist:
            return False

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

            return sites

        except DoesNotExist:
            return False

    def get_asset_by_serial(self, assetSerial=None):

        try:
            data = Asset.get(Asset.assetSerial == assetSerial).assetConfigId
            return data

        except DoesNotExist:
            return False

    def update_asset_site_mapping(self, assetSerial=None, assetConfigId=None):

        query = Asset.update(assetSerial=assetSerial).where(Asset.assetConfigId == assetConfigId)
        query.execute()
        database.close()

        return True

    def add_group(self, groupName, groupConfig, groupDescr):

        try:

            new_group = Group.create(groupName=groupName, groupDescr=groupDescr)
            new_group.save()
            database.close()
            return True

        except IntegrityError as ie:
            self._logger.info('YAPTBACKEND-[%s]: %s', groupName, ie)
            return False

    def get_group_by_name(self, groupName):
        pass

    def get_groups(self):

        groups = list()

        try:
            query = prefetch(Group.select())

            for group in query:
                groupData = {'groupId': group.groupId, 'groupName': group.groupName, 'groupDescr': group.groupDescr}
                groups.append(groupData)

            return groups

        except DoesNotExist:
            return False


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


class Site(BaseModel):
    siteId = CharField(unique=True, primary_key=True)
    siteName = CharField(default='')
    siteDescr = CharField(default='')


class Asset(BaseModel):
    assetId = IntegerField(unique=True, primary_key=True)
    assetSiteId = ForeignKeyField(Site, related_name='refSite')
    # assetSerial should be unique. How to initialize unique key with empty value?
    assetSerial = CharField(null=True)
    assetConfigId = CharField(unique=True, default='')
    assetDescr = CharField(default='')


class Group(BaseModel):
    groupId = IntegerField(unique=True, primary_key=True)
    groupName = CharField(unique=True, default='')
    groupDescr = CharField(default='')


def taskFactory(dbName=None, fields=None, refName=None):
    class DynamicTable(BaseModel):
        owner = ForeignKeyField(Device, related_name=refName, unique=True, primary_key=True)

        class Meta:
            validate_backrefs = False
            db_table = dbName

    for field in fields:
        CharField(default='Waiting').add_to_class(DynamicTable, field)
    return DynamicTable
