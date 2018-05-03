# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import LogSpace as logmsg
from lib.tasks.task import Task
from lib.tools import Tools


class PublishTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):

        super(PublishTask, self).__init__(sample_device=sample_device, shared=shared)
        self.task_type = c.TASK_TYPE_PROVISION
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(PublishTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                              logmsg.PUBLISH_INIT.format(self.sample_device.deviceSerial)))

        policy_data = c.SRC.get_fw_policy_by_name(self.sample_device.deviceName)

        if policy_data == c.SRC_RESPONSE_FAILURE:

            self.sample_device.deviceTasks.taskState[self.task_name] = c.SRC_RESPONSE_FAILURE
            self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE

        else:

            self.sample_device.deviceTasks.taskState[self.task_name] = 'Publish rule'
            URI = 'api/juniper/sd/fwpolicy-management/publish?update=true'
            HEADER = {
                'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.publish+xml;version=1;charset=UTF-8'}
            BODY = '<publish><policy-ids><policy-id>{0}</policy-id></policy-ids></publish>'.format(policy_data['pid'])

            response = c.SRC.post(URI, HEADER, BODY)

            if response.status_code == 500:
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.PUBLISH_NOK.format(self.sample_device.deviceSerial, response.text)))
            elif response.status_code == 202:

                if response.text is not None:

                    xmlRoot = ET.fromstring(response.text)
                    jobId = xmlRoot.find('id').text
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.PUBLISH_DONE.format(self.sample_device.deviceSerial, str(jobId))))
                    self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_DONE
                    self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_DONE

                else:
                    self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                          logmsg.PUBLISH_RESP_NOK.format(response.text,
                                                                                     response.code)))
            else:
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.PUBLISH_RESP_UNKNOWN.format(response.status_code)))

    def post_run_task(self):
        pass
