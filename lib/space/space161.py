# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from jinja2 import Template
from jnpr.junos.exception import *
from lib.space.src import SpaceRestConnector
from lib.tools import Tools


class Space161(SpaceRestConnector):
    def __init__(self, space_ip=None, space_user=None, space_password=None):
        super(Space161, self).__init__(space_ip=space_ip, space_user=space_user, space_password=space_password)
        self.logger.info('PROVSPACE: Junos Space <16.1> plugin successfully loaded')

    def add_fw_policy(self, body):

        URI = 'api/juniper/sd/policy-management/firewall/policies'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.policy-management.firewall.policy+xml;version=2;charset=UTF-8'}
        response = self.post(URI, HEADER, body)

        return response

    def add_fw_policy_rule_lrr(self, sample_device):
        pass

    def add_fw_rule(self, body):
        pass

    def add_adress_object(self, body):
        pass

    def add_service_object(self, body):
        pass

    def add_modeled_device_instance(self, instance_id, device_count=1):
        """

        :param instance_id:
        :param device_count:
        :return:
        """
        pass

    def get_fw_policy_by_id(self, pid):

        URI = 'api/juniper/sd/policy-management/firewall/policies/ ' + pid
        HEADER = {'Accept': 'application/vnd.juniper.sd.policy-management.firewall.policy+xml;version=2;q=0.02'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        policy_id = 0
        policy_name = ''
        policy_version = 0

        for child in xmlRoot:

            if child.tag == 'id':
                policy_id = child.text
            if child.tag == 'name':
                policy_name = child.text
            if child.tag == 'edit-version':
                policy_version = child.text

        policy_data = {'pid': policy_id, 'name': policy_name, 'version': policy_version}

        return policy_data

    def get_fw_policy_by_name(self, deviceName):

        URI = 'api/juniper/sd/policy-management/firewall-policies?filter=(global eq \'' + deviceName + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.policy-management.firewall-policies+xml;version=1;q=0.01'}
        xmlData = self.get(URI, HEADER)

        if xmlData.status_code == 404:

            return Tools.SRC_RESPONSE_FAILURE

        else:

            xmlRoot = ET.fromstring(xmlData.text)

            pid = 0
            mid = 0

            for child in xmlRoot:
                pid = child.find('id').text
            #
            URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + str(pid) + '/firewall-rules'
            HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-rules+xml;version=1;q=0.0'}
            xmlData = self.get(URI, HEADER)

            if xmlData.status_code == 404:

                return Tools.SRC_RESPONSE_FAILURE

            else:

                xmlRoot = ET.fromstring(xmlData.text)

                for child in xmlRoot:
                    mid = child.find('id').text

                data = {'pid': pid, 'mid': mid}

                return data

    def get_fw_policy_member_by_id(self, pid, mid):
        pass

    def get_fw_rule_by_name(self, name, gid):
        pass

    def get_address_by_name(self, name):
        pass

    def get_service_by_name(self, name):
        pass

    def get_device_by_name(self, name):
        pass

    def get_rule_profile_by_name(self, name):
        pass

    def get_modeled_device_instance_id(self, model):
        """

        :param model:
        :return:
        """
        pass

    def publish_policy(self, body):
        pass

    def publish_and_update_policy(self, body):
        pass

    def delete_fw_policy_by_id(self, pid):
        pass

    def delete_fw_rule(self, body):
        pass

    def delete_address_object_by_id(self, id):
        pass

    def delete_service_object_by_id(self, id):
        pass

    def discover_device(self, body):

        URI = 'api/space/device-management/discover-devices?queue==https://' + Tools.conf.JUNOSSPACE.Ip + '/api/hornet-q/queues/jms.queue.yaptQueue'
        HEADER = {
            'Content-Type': 'application/vnd.net.juniper.space.device-management.discover-devices-request+xml;version=6;charset=UTF-8 '}

        self.post(URI, HEADER, body)

    def assign_device(self, body, pid):

        URI = 'api/juniper/sd/policy-management/firewall/policies/' + pid + '/assign-devices'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.policy-management.assign-devices+xml;version=2;charset=UTF-8'}

        self.post(URI, HEADER, body)

    def lock_fw_policy(self, pid):

        URI = 'api/juniper/sd/policy-management/firewall/policies/' + pid + '/lock'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.lock-management.lock+xml;version=1;charset=UTF-8'}

        response = self.post(URI, HEADER, "")

        return response

    def unlock_fw_policy(self, pid):

        URI = 'api/juniper/sd/policy-management/firewall/policies/' + pid + '/unlock'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.lock-management.lock+xml;version=1;charset=UTF-8'}

        self.post(URI, HEADER, "")

    def createIPSecVPN(self, body):
        pass

    def modifyIPSecVPN(self, body):
        pass

    def discover_by_space(self, sample_device=None, shared=None):

        with Tools.lrr_lock:

            Tools.lrr_counter += 1

        queue = 'yaptDiscover' + str(Tools.lrr_counter)
        self.create_hornet_queue(queue)
        self.logger.info('PROVSPACE-[%s]: Start Junos Space discovery process for device: %s', sample_device.deviceIP,
                         sample_device.deviceIP)
        sample_device.deviceProvisionTasks.taskState['Discovery'] = 'Discover'

        URI = 'api/space/device-management/discover-devices?queue=https://' + Tools.conf.JUNOSSPACE.Ip + \
              '/api/hornet-q/queues/jms.queue.' + queue
        HEADER = {
            'Content-Type': 'application/vnd.net.juniper.space.device-management.discover-devices+xml;version=2;charset=UTF-8'}

        template = Template(open(Tools.conf.JUNOSSPACE.TemplateDir + '/discoverDevice.j2').read())
        BODY = template.render(ip_address=sample_device.deviceIP, user=Tools.conf.YAPT.DeviceUsr,
                               password=Tools.get_password(Tools.YAPT_PASSWORD_TYPE_DEVICE))

        response = self.post(URI, HEADER, BODY)

        if response is not None:

            xmlRoot = ET.fromstring(response.text)
            jobId = xmlRoot.find('id').text

            self.logger.info('PROVSPACE-[%s]: Change is in progress - check job ID %s', sample_device.deviceIP,
                             str(jobId))

            URI = 'api/hornet-q/queues/jms.queue.' + queue
            HEADER = ''
            BODY = ''

            response = self.head(URI, HEADER, BODY)

            pull_consumers = response.headers['msg-pull-consumers']
            pattern = r'https://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(.*)'
            regex = re.compile(pattern, re.MULTILINE)
            result = re.findall(regex, pull_consumers)

            URI = result[0]
            HEADER = {'Accept-Wait': '5'}
            BODY = ''

            response = self.post(URI, HEADER, BODY)

            while True:

                if 'msg-consume-next' in response.headers:

                    msg_consume_next = response.headers['msg-consume-next']
                    pattern = r'https://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(.*)'
                    regex = re.compile(pattern, re.MULTILINE)
                    result = re.findall(regex, msg_consume_next)
                    URI = result[0]
                    response = self.post(URI, HEADER, BODY)

                    if response.status_code == 503:

                        self.logger.info('PROVSPACE-[%s]: Discovery for device %s state is: %s',
                                         sample_device.deviceIP, sample_device.deviceIP,
                                         'Waiting for Junos Space response')
                        sample_device.deviceProvisionTasks.taskState['Discovery'] = 'Waiting for response'

                    elif response.status_code == 200:

                        xmlRoot = ET.fromstring(response.text)
                        taskId = xmlRoot.find('taskId').text

                        if jobId == taskId:

                            state = xmlRoot.findall("./state")

                            if state[0].text == 'INPROGRESS':

                                self.logger.info('PROVSPACE-[%s]: Discovery for device %s state is: %s',
                                                 sample_device.deviceIP, sample_device.deviceIP, state[0].text)
                                sample_device.deviceProvisionTasks.taskState['Discovery'] = state

                            elif state[0].text == 'DONE':

                                self.logger.info('PROVSPACE-[%s]: Discovery for device %s state is: %s',
                                                 sample_device.deviceIP, sample_device.deviceIP, state)

                                self.logger.info(
                                    'PROVSPACE-[%s]: Device discovery done for device %s. Cleaning up queues',
                                    sample_device.deviceIP, sample_device.deviceIP)

                                URI = 'api/hornet-q/queues/jms.queue.' + queue
                                HEADER = ''

                                # Todo: Check response code in response is 204 --> OK
                                # Todo: If not 204 what todo?
                                response = self.delete(URI, HEADER)

                                if Tools.lrr_counter > 0:
                                    with Tools.lrr_lock:
                                        Tools.lrr_counter -= 1

                                summary = xmlRoot.find('summary').text

                                self.logger.info('PROVSPACE-[%s]: Discovery for device %s Summary: %s',
                                                 sample_device.deviceIP, sample_device.deviceIP, summary)

                                pattern = r'Job was cancelled by user\s.*'

                                regex = re.compile(pattern, re.MULTILINE)
                                result = re.findall(regex, summary)

                                if result:
                                    self.logger.info('PROVSPACE: Seems to be the job was canceled by Space user.')
                                    break

                                else:

                                    pattern = r'Number\sof\s(.*?):\s(\d)<br>'

                                    regex = re.compile(pattern, re.MULTILINE)
                                    result = re.findall(regex, summary)
                                    result = dict((x, int(y)) for x, y in result)

                                    # Number should always be one because we are discovering only one device. So we can use
                                    # this getting info about discovery state for current device
                                    #
                                    # Number of scanned IP: 1<br>
                                    # Number of Device Managed: 1<br>
                                    # Number of Discovery succeeded: 1<br>
                                    # Number of Already Managed: 0<br>
                                    # Number of Add Device failed: 0<br>
                                    # Number of Skipped: 0<br>
                                    # Number of scanned IP: 1<br>Number of Discovery succeeded: 0<br>Number of Add Device failed: 0<br>Number of Already Managed: 1<br>Number of Skipped: 0<br>Number of Device Managed: 0<br>

                                    if result[Tools.SPACE_DISCOVERY_NOAM] != 0:
                                        sample_device.deviceProvisionTasks.taskState['Discovery'] = 'Already managed'
                                        self.logger.info('PROVSPACE: Discovery for device %s state is: Already managed',
                                                         sample_device.deviceIP)
                                        shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_DONE
                                    elif result[Tools.SPACE_DISCOVERY_NOADF] != 0:
                                        sample_device.deviceProvisionTasks.taskState['Discovery'] = 'Failed'
                                        self.logger.info('PROVSPACE: Discovery for device %s state is: Failed',
                                                         sample_device.deviceIP)
                                        shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                                    elif result[Tools.SPACE_DISCOVERY_NODS] != 0:
                                        sample_device.deviceProvisionTasks.taskState['Discovery'] = 'Done'
                                        self.logger.info('PROVSPACE: Discovery for device %s state is: Succeeded',
                                                         sample_device.deviceIP)
                                        shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_DONE
                                    elif result[Tools.SPACE_DISCOVERY_NOS] != 0:
                                        sample_device.deviceProvisionTasks.taskState['Discovery'] = 'Skipped'
                                        self.logger.info('PROVSPACE: Discovery for device %s state is: Skipped',
                                                         sample_device.deviceIP)
                                        shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_DONE

                                    break

                            else:
                                self.logger.info('PROVSPACE: Got unknown Junos Space state in response')
                                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                    else:
                        self.logger.info('PROVSPACE: Got unknown status code in Junos Space response')
                        shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                else:
                    self.logger.info('PROVSPACE: Got unknown status code in Junos Space response')
                    shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                    break
        else:
            self.logger.info('PROVSPACE: Bad status code in Junos Space response')
            shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
