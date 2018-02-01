# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import weakref

import jsonpickle

from lib.amqp.amqpmessage import AMQPMessage
import lib.constants as c


class SampleDevice(object):
    """
    SampleDevice class represents a device to be provisioned.
    """

    # ------------------------------------------------------------------------
    # property: deviceName
    # ------------------------------------------------------------------------

    @property
    def deviceName(self):
        """
        :returns: the name of the device.
        """
        return self.__deviceName

    @deviceName.setter
    def deviceName(self, value):
        self.__deviceName = value

    # ------------------------------------------------------------------------
    # property: deviceModel
    # ------------------------------------------------------------------------

    @property
    def deviceModel(self):
        """
        :returns: the model of the device.
        """
        return self.__deviceModel

    @deviceModel.setter
    def deviceModel(self, value):
        self.__deviceModel = value

    # ------------------------------------------------------------------------
    # property: deviceSerial
    # ------------------------------------------------------------------------

    @property
    def deviceSerial(self):
        """
        :returns: the serial number of the device.
        """
        return self.__deviceSerial

    @deviceSerial.setter
    def deviceSerial(self, value):
        self.__deviceSerial = value

    # ------------------------------------------------------------------------
    # property: softwareVersion
    # ------------------------------------------------------------------------

    @property
    def softwareVersion(self):
        """
        :returns: the software version of the device.
        """
        return self.__softwareVersion

    @softwareVersion.setter
    def softwareVersion(self, value):
        self.__softwareVersion = value

    # ------------------------------------------------------------------------
    # property: deviceIP
    # ------------------------------------------------------------------------

    @property
    def deviceIP(self):
        """
        :returns: the IP address of the device.
        """
        return self.__deviceIP

    @deviceIP.setter
    def deviceIP(self, value):
        self.__deviceIP = value

    # ------------------------------------------------------------------------
    # property: deviceTimeStamp
    # ------------------------------------------------------------------------

    @property
    def deviceTimeStamp(self):
        """
        :returns: represents device last seen.
        """
        return self.__deviceTimeStamp

    @deviceTimeStamp.setter
    def deviceTimeStamp(self, value):
        self.__deviceTimeStamp = value

    # ------------------------------------------------------------------------
    # property: deviceConnection
    # ------------------------------------------------------------------------

    @property
    def deviceConnection(self):
        """
        :returns: the deviceConnection reference of the device.
        """
        return self.__deviceConnection

    @deviceConnection.setter
    def deviceConnection(self, value):
        self.__deviceConnection = value

    # ------------------------------------------------------------------------
    # property: deviceTasks
    # ------------------------------------------------------------------------

    @property
    def deviceTasks(self):
        """
        :returns: the provisioning tasks and their status messages
        (Software/Filecp/Configuration/Cert/Discovery/Policy/Assign/Rules/Publish)
        """
        return self.__deviceTasks

    # ------------------------------------------------------------------------
    # property: deviceIsRebooted
    # ------------------------------------------------------------------------

    @property
    def deviceIsRebooted(self):
        """
        :returns: after images update done set prop to true so we do not loop through image update process again
        """
        return self.__deviceIsRebooted

    @deviceIsRebooted.setter
    def deviceIsRebooted(self, value):
        self.__deviceIsRebooted = value

    # ------------------------------------------------------------------------
    # property: deviceConfiguration
    # ------------------------------------------------------------------------

    @property
    def deviceConfiguration(self):
        """
        :returns: device configuration
        """
        return self.__deviceConfiguration

    @deviceConfiguration.setter
    def deviceConfiguration(self, value):
        self.__deviceConfiguration = value

    # ------------------------------------------------------------------------
    # property: deviceProvisionProgress
    # ------------------------------------------------------------------------

    @property
    def deviceTaskProgress(self):
        """
        :returns: device configuration
        """
        return self.__deviceTaskProgress

    @deviceTaskProgress.setter
    def deviceTaskProgress(self, value):
        self.__deviceTaskProgress = value

    # ------------------------------------------------------------------------
    # property: deviceStatus
    # ------------------------------------------------------------------------

    @property
    def deviceStatus(self):
        """
        :returns: deviceStatus explains if device is a complete new device or already provisioned device (New/Done/Failed)
        """
        return self.__deviceStatus

    @deviceStatus.setter
    def deviceStatus(self, value):
        self.__deviceStatus = value

    # ------------------------------------------------------------------------
    # property: deviceProvisionProgress
    # ------------------------------------------------------------------------

    @property
    def is_callback(self):
        """
        :returns: device provision task progress
        """
        return self.__is_callback

    @is_callback.setter
    def is_callback(self, value):
        self.__is_callback = value

    # ------------------------------------------------------------------------
    # property: deviceGroup
    # ------------------------------------------------------------------------

    @property
    def deviceGroup(self):
        """
        :returns: the name of the device group.
        """
        return self.__deviceGroup

    @deviceGroup.setter
    def deviceGroup(self, value):
        self.__deviceGroup = value

    # ------------------------------------------------------------------------
    # property: deviceConfData
    # ------------------------------------------------------------------------

    @property
    def deviceConfData(self):
        """
        :returns: current device config data.
        """
        return self.__deviceConfData

    @deviceConfData.setter
    def deviceConfData(self, value):
        self.__deviceConfData = value

    # ------------------------------------------------------------------------
    # property: deviceConfFile
    # ------------------------------------------------------------------------

    @property
    def deviceConfFile(self):
        """
        :returns: current device config data filename.
        """
        return self.__deviceConfFile

    @deviceConfFile.setter
    def deviceConfFile(self, value):
        self.__deviceConfFile = value

    # ------------------------------------------------------------------------
    # property: deviceGroupData
    # ------------------------------------------------------------------------

    @property
    def deviceGroupData(self):
        """
        :returns: current device group config data.
        """
        return self.__deviceGroupData

    @deviceGroupData.setter
    def deviceGroupData(self, value):
        self.__deviceGroupData = value

    # ------------------------------------------------------------------------
    # property: deviceGroupFile
    # ------------------------------------------------------------------------

    @property
    def deviceGroupFile(self):
        """
        :returns: current device group config data filename.
        """
        return self.__deviceGroupFile

    @deviceGroupFile.setter
    def deviceGroupFile(self, value):
        self.__deviceGroupFile = value

    # ------------------------------------------------------------------------
    # property: deviceTemplate
    # ------------------------------------------------------------------------

    @property
    def deviceTemplate(self):
        """
        :returns: current device config template.
        """
        return self.__deviceTemplate

    @deviceTemplate.setter
    def deviceTemplate(self, value):
        self.__deviceTemplate = value

    # ------------------------------------------------------------------------
    # property: deviceTemplateFile
    # ------------------------------------------------------------------------

    @property
    def deviceTemplateFile(self):
        """
        :returns: current device config template filename.
        """
        return self.__deviceTemplateFile

    @deviceTemplateFile.setter
    def deviceTemplateFile(self, value):
        self.__deviceTemplateFile = value

    # ------------------------------------------------------------------------
    # property: deviceSourcePlugin
    # ------------------------------------------------------------------------

    @property
    def deviceSourcePlugin(self):
        """
        :returns: attached device source plugin
        """
        return self.__deviceSourcePlugin

    @deviceSourcePlugin.setter
    def deviceSourcePlugin(self, value):
        self.__deviceSourcePlugin = value

    # ------------------------------------------------------------------------
    # property: deviceTaskSeq
    # ------------------------------------------------------------------------

    @property
    def deviceTaskSeq(self):
        """
        :returns: Devices Provision Task Sequence. Used later on for UI interface
        """
        return self.__deviceTaskSeq

    @deviceTaskSeq.setter
    def deviceTaskSeq(self, value):
        self.__deviceTaskSeq = value

    # ------------------------------------------------------------------------
    # property: deviceOssId
    # ------------------------------------------------------------------------

    @property
    def deviceOsshId(self):
        """
        :returns: Ossh device ID. Used alter on for NFX VNF use cases
        """
        return self.__deviceOsshId

    @deviceOsshId.setter
    def deviceOsshId(self, value):
        self.__deviceOsshId = value

    def __init__(self, deviceIP, deviceTimeStamp, deviceStatus, deviceSourcePlugin):
        """
        :param deviceIP: device IP address
        :param deviceTimeStamp: creation timestamp
        :param deviceStatus: new device or changed device or done device
        :return:
        """
        self.__deviceName = None
        self.__deviceModel = None
        self.__deviceSerial = None
        self.__softwareVersion = None
        self.__deviceIP = deviceIP
        self.__deviceTimeStamp = deviceTimeStamp
        self.__deviceConnection = None
        self.__deviceIsRebooted = False
        self.__deviceConfiguration = None
        self.__deviceStatus = deviceStatus
        self.__deviceTaskProgress = 0
        self.__deviceGroup = None
        self.__deviceConfData = None
        self.__deviceConfFile = None
        self.__deviceGroupData = None
        self.__deviceGroupFile = None
        self.__deviceTemplate = None
        self.__deviceTemplateFile = None
        self.__deviceOsshId = None
        self.__deviceSourcePlugin = deviceSourcePlugin
        self.__deviceTaskSeq = None
        self.__deviceTasks = TaskState()
        self.__is_callback = True
        self.__device_task_seq = dict()
        # We need back ref to sampleDevice in TasksState. Should be a better way doing this.
        self.__device_task_seq['sampleDevice'] = self
        self.__deviceTasks.taskState = self.__device_task_seq

    def device_to_json(self, action=None):
        deviceTasksStates = [i for i in self.deviceTasks.taskState.items() if
                             i[0] != 'sampleDevice']
        deviceTasksStates = sorted(deviceTasksStates,
                                   key=lambda t: self.deviceTaskSeq.index(t[0]))

        data = {
            "deviceName": self.deviceName, "softwareVersion": self.softwareVersion,
            "deviceIP": self.deviceIP, "deviceSerial": self.deviceSerial,
            "deviceModel": self.deviceModel, "deviceTimeStamp": self.deviceTimeStamp,
            "deviceConnection": self.deviceConnection,
            "deviceTasksStates": deviceTasksStates,
            "deviceConfiguration": self.deviceConfiguration,
            "deviceStatus": self.deviceStatus,
            "deviceSourcePlugin": self.deviceSourcePlugin,
            "taskProgress": self.deviceTaskProgress,
            "deviceGroup": self.deviceGroup,
            "deviceTaskSequence": self.deviceTaskSeq,
            "action": action
        }

        return jsonpickle.dumps(data, unpicklable=False)


class TaskStateObserver(object):
    def __init__(self, item=None, callback=None, **kwargs):

        self.item = item
        self.callback = callback
        self.kwargs = kwargs
        self.kwargs.update({
            'callback': callback,
        })

        self._sample_device = None
        self._value = None
        self._instance_to_name_mapping = {}
        self._instance = None
        self._parent_observer = None
        self._value_parent = None
        self._value_index = None

    @property
    def value(self):
        """Returns the content of attached data.
        """
        return self._value

    def _get_attr_name(self, instance):
        """To respect DRY methodology, we try to find out, what the original name of the descriptor is and
        use it as instance variable to store actual data.

        Args:
            instance: instance of the object

        Returns: (str): attribute name, where `Observer` will store the data
        """

        if instance in self._instance_to_name_mapping:
            return self._instance_to_name_mapping[instance]

        for attr_name, attr_value in instance.__class__.__dict__.iteritems():

            if attr_value is self:
                self._instance_to_name_mapping[weakref.ref(instance)] = attr_name

                return attr_name

    def __get__(self, instance, owner):
        attr_name = self._get_attr_name(instance)
        attr_value = instance.__dict__.get(attr_name, self.item)
        observer = self.__class__(**self.kwargs)
        # Todo: Change _value to only have tasks?
        observer._value = attr_value
        observer._instance = instance
        observer._sample_device = attr_value['sampleDevice']
        return observer

    def __set__(self, instance, value):
        attr_name = self._get_attr_name(instance)
        instance.__dict__[attr_name] = value
        self._sample_device = value['sampleDevice']
        self._value = value
        self._instance = instance

    def __getitem__(self, key):

        observer = self.__class__(**self.kwargs)
        observer._value = self._value[key]
        observer._parent_observer = self
        observer._value_parent = self._value
        observer._value_index = key
        return observer.value

    # Todo: check if __setitem__ is the right place for callback?
    def __setitem__(self, key, value):

        self._value[key] = value
        if self._sample_device.is_callback:
            self.update_backend(key)

    def update_backend(self, key):

        """Calls callback action. Notify that data content has changed.
        """
        # we want to evoke the very first observer with complete set of data, not the nested one
        if self._parent_observer:
            self._parent_observer.update_backend(key)
        else:
            if self.callback:
                self.callback(self, self._instance, self._sample_device, key, self._value[key])

    def __getattr__(self, item):
        """Mock behaviour of data attach to `Observer`. If certain behaviour mutate attached data, additional
        wrapper comes into play, evoking attached callback.
        """

        def observe(o, f):
            def wrapper(*args, **kwargs):
                result = f(*args, **kwargs)
                return result

            return wrapper

        attr = getattr(self._value, item)

        if item in (['clear', 'pop', 'update']):  # dict methods
            return observe(self, attr)
        return attr


def action(self, instance, sample_device, task_name, task_state):
    from lib.processor import BackendClientProcessor
    backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
    dev_conn = sample_device.deviceConnection
    sample_device.deviceConnection = hex(id(sample_device.deviceConnection))

    if isinstance(instance, TaskState):

        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_UPDATE_TASK_STATE,
                              payload={'sample_device': sample_device, 'taskName': task_name,
                                       'taskState': task_state['taskState'],
                                       'taskStateMsg': task_state['taskStateMsg']},
                              source=task_name)
        backendp.call(message=message)

    else:
        self._logger.info('Unknown task type %s. Can\'t update backend', instance)

    sample_device.deviceConnection = dev_conn


class TaskState(object):
    taskState = TaskStateObserver(item=None, callback=action)
