# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import time

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import yaml
from jinja2 import Template
from jnpr.junos.exception import *

from lib.space.src import SpaceRestConnector
from lib.logmsg import LogSpace as logmsg
import lib.constants as c
from lib.tools import Tools


class Space151(SpaceRestConnector):
    def __init__(self, space_ip=None, space_user=None, space_password=None):
        super(Space151, self).__init__(space_ip=space_ip, space_user=space_user, space_password=space_password)
        self.logger.info(Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_LOADED.format('15.1')))

    def add_fw_policy(self, body):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.firewall-policy+xml;version=1;charset=UTF-8'}
        response = self.post(URI, HEADER, body)

        return response

    def add_fw_policy_rule_lrr(self, sample_device):

        queue = 'yaptPublish' + str(c.lrr_counter)
        policy_data = self.get_fw_policy_by_name(sample_device.deviceName)
        time.sleep(self.__rest_timeout)
        address_data_src = self.get_address_by_name('Any')
        time.sleep(self.__rest_timeout)
        address_data_dst = self.get_address_by_name('Any')
        time.sleep(self.__rest_timeout)
        service_data = self.get_service_by_name('Any')
        time.sleep(self.__rest_timeout)
        profile_data = self.get_rule_profile_by_name('All Logging Enabled')
        time.sleep(self.__rest_timeout)

        policy_data = self.get_fw_policy_member_by_id(policy_data['pid'], policy_data['mid'])
        time.sleep(self.__rest_timeout)
        isNotSourceIdentity = '<source-identities/>'
        description = 'Default deny all rule - created by YAPT'
        template = Template(open('lib/templates/jinja2/fwdefaultrule.j2').read())
        ruleVars = yaml.load(open('lib/templates/jinja2/fwdefaultrule.yml').read())

        body = template.render(ruleVars, version=policy_data['version'], pid=policy_data['pid'],
                               description=description, gid=policy_data['gid'], gpname=policy_data['name'],
                               srcAddrName=address_data_src['name'], srcAddrId=address_data_src['id'],
                               identities=isNotSourceIdentity, dstAddrName=address_data_dst['name'],
                               dstAddrId=address_data_dst['id'], serviceId=service_data['id'],
                               serviceName=service_data['name'], rpname=profile_data['name'],
                               rpid=profile_data['id'])

        self.lock_fw_policy(policy_data['pid'])
        time.sleep(self.__rest_timeout)
        self.add_fw_rule(body)
        time.sleep(self.__rest_timeout)
        self.unlock_fw_policy(policy_data['pid'])
        time.sleep(self.__rest_timeout)

        ##################
        # Publish Rule   #
        ##################
        self.create_hornet_queue(queue)
        sample_device.deviceProvisionTasksStates['Rule'] = 'Publish rule'
        URI = 'api/juniper/sd/fwpolicy-management/publish?update=true?queue=https://' + c.conf.JUNOSSPACE.IP + '/api/hornet-q/queues/jms.queue.' + queue
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.publish+xml;version=1;charset=UTF-8'}
        BODY = '<publish><policy-ids><policy-id>' + str(policy_data['pid']) + '</policy-id></policy-ids></publish>'

        response = self.post(URI, HEADER, BODY)

        xmlRoot = ET.fromstring(response.text)
        jobId = xmlRoot.find('id').text

        self.logger.info('PROVSPACE-[%s]: Change is in progress - check job ID %s', sample_device.deviceIP,
                         str(jobId))

        URI = 'api/hornet-q/queues/jms.queue.' + queue
        HEADER = ''
        BODY = ''

        response = self.head(URI, HEADER, BODY)
        time.sleep(self.__rest_timeout)

        pull_consumers = response.headers['msg-pull-consumers']
        pattern = r'https://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(.*)'
        regex = re.compile(pattern, re.MULTILINE)
        result = re.findall(regex, pull_consumers)

        URI = result[0]
        HEADER = {'Accept-Wait': '3'}
        BODY = ''

        response = self.post(URI, HEADER, BODY)
        state = None

        while True:

            if state == 'DONE':
                self.logger.info('PROVSPACE-[%s]: Publishing policy for device %s done', sample_device.deviceIP,
                                 sample_device.deviceIP)
                URI = 'api/hornet-q/queues/jms.queue.' + queue
                HEADER = ''
                response = self.delete(URI, HEADER)
                break

            else:

                msg_consume_next = response.headers['msg-consume-next']
                pattern = r'https://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/(.*)'
                regex = re.compile(pattern, re.MULTILINE)
                result = re.findall(regex, msg_consume_next)
                URI = result[0]
                response = self.post(URI, HEADER, BODY)

                if response.status_code == 503:
                    self.logger.info('PROVSPACE-[%s]: Timed out waiting for message receive for device %s',
                                     sample_device.deviceIP, sample_device.deviceIP)

                    if sample_device.deviceProvisionTasksStates['Rule'] == 'Waiting for Space response':
                        pass
                    else:
                        sample_device.deviceProvisionTasksStates['Rule'] = 'Waiting for Space response'
                    time.sleep(self.__rest_timeout)
                else:

                    xmlRoot = ET.fromstring(response.text)
                    taskId = xmlRoot.find('taskId').text

                    if jobId == taskId:
                        state = xmlRoot.find('state').text
                        self.logger.info('PROVSPACE-[%s]: Publishing policy for device %s state is: %s',
                                         sample_device.deviceIP, sample_device.deviceIP, state)
                        sample_device.deviceProvisionTasksStates['Rule'] = state

                    else:
                        self.logger.info('PROVSPACE-[%s]: Found other job with ID %s ', sample_device.deviceIP,
                                         taskId)
                        time.sleep(self.__rest_timeout)

    def add_fw_rule(self, body):

        URI = 'api/juniper/sd/fwpolicy-management/modify-rules'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.modify-rules+xml;version=1;charset=UTF-8'}
        self.post(URI, HEADER, body)

    def add_adress_object(self, body):

        URI = 'api/juniper/sd/address-management/addresses'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.address-management.address+xml;version=1;charset=UTF-8'}
        self.post(URI, HEADER, body)

    def add_service_object(self, body):

        URI = 'api/juniper/sd/service-management/services'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.service-management.service+xml;version=1;charset=UTF-8'}
        self.post(URI, HEADER, body)

    def add_modeled_device_instance(self, instance_id, device_count=1):
        """

        :param instance_id:
        :param device_count:
        :return:
        """

        self.logger.info('PROVSPACE: Start Junos Space provisioning process for instance: %s', instance_id)

        URI = 'api/space/device-management/modeled-device-management/modeled-instances/' + instance_id + '/add-more-devices'
        BODY = "<add-more-devices-request><device-count>" + str(
            device_count) + "</device-count></add-more-devices-request>"

        HEADER = {'Content-Type': 'application/vnd.net.juniper.space.device-management.modeled-device-management.'
                                  'add-more-devices-request+xml;version=1;charset=UTF-8'}

        response = self.post(URI, HEADER, BODY)

        if response.status_code == 500:
            self.logger.info('PROVSPACE: Error adding device to instance %s', instance_id)
            return c.SRC_RESPONSE_FAILURE

        else:

            xmlRoot = ET.fromstring(response.text)
            jobId = xmlRoot.find('id').text
            self.logger.info('PROVSPACE: Change is in progress - check job ID %s', str(jobId))
            return jobId

    def get_fw_policy_by_id(self, pid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + pid
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-policies+xml;version=1;q=0.01'}

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

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies?filter=(global eq \'' + deviceName + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-policies+xml;version=1;q=0.01'}
        xmlData = self.get(URI, HEADER)

        if xmlData.status_code == 404:

            return c.SRC_RESPONSE_FAILURE

        else:

            xmlRoot = ET.fromstring(xmlData.text)

            pid = 0
            mid = 0

            for child in xmlRoot:
                pid = child.find('id').text

            URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + str(pid) + '/firewall-rules'
            HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-rules+xml;version=1;q=0.0'}
            time.sleep(5)
            xmlData = self.get(URI, HEADER)

            if xmlData.status_code == 404:

                return c.SRC_RESPONSE_FAILURE

            else:

                xmlRoot = ET.fromstring(xmlData.text)

                for child in xmlRoot:
                    mid = child.find('id').text

                data = {'pid': pid, 'mid': mid}

                return data

    def get_fw_policy_member_by_id(self, pid, mid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + pid
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-policy+xml;version=1;q=0.01'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        policy_id = 0
        policy_name = ''
        policy_version = 0
        group_id = 0

        for child in xmlRoot:

            if child.tag == 'id':
                policy_id = child.text

            if child.tag == 'name':
                policy_name = child.text

            if child.tag == 'edit-version':
                policy_version = child.text

        URI = 'api/juniper/sd/fwpolicy-management/firewall-rules/' + mid + '/members/'
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-rules+xml;version=1;q=0.01'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        for child in xmlRoot:

            rule_group_type = child.find('rule-group-type').text
            rule_group__name = child.find('name').text
            rule_group_id = child.find('id').text

            if rule_group_type == 'DEVICE':

                if rule_group__name == 'Device Rules':
                    group_id = rule_group_id

        data = {'pid': policy_id, 'name': policy_name, 'version': policy_version, 'mid': mid, 'gid': group_id}

        return data

    def get_fw_rule_by_name(self, name, gid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-rules/' + gid + '/members?filter=(global eq \'' + name + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-rules+xml;version=1;q=0.01'}

        rule_id = 0
        rule_name = 0
        rule_group_id = 0
        rule_policy_name = 0

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        for child in xmlRoot.findall('firewall-rule'):
            rule_id = child.find('id').text

        URI = 'api/juniper/sd/fwpolicy-management/firewall-rules/' + str(rule_id)
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.firewall-rule+xml;version=1;q=0.01'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        for child in xmlRoot.findall('firewall-rule'):
            rule_name = child.find('name').text
            rule_group_id = child.find('rule-group-id').text
            rule_policy_name = child.find('policy-name').text

        rule_data = {'name': rule_name, 'id': rule_id, 'gid': rule_group_id, 'rpname': rule_policy_name}

        return rule_data

    def get_address_by_name(self, name):

        URI = 'api/juniper/sd/address-management/addresses?filter=(name eq \'' + name + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.address-management.address-refs+xml;version=1;q=0.01'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        address_name = 0
        address_ip = 0
        address_id = 0
        address_type = 0

        if 'Any' in name:

            for neighbor in xmlRoot.findall('address'):
                address_name = neighbor.find('name').text
                address_id = neighbor.find('id').text
                address_type = neighbor.find('address-type').text

        else:

            for neighbor in xmlRoot.findall('address'):
                address_name = neighbor.find('name').text
                address_ip = neighbor.find('ip-address').text
                address_id = neighbor.find('id').text
                address_type = neighbor.find('address-type').text

        address_data = {'name': address_name, 'ip': address_ip, 'id': address_id, 'type': address_type}

        return address_data

    def get_service_by_name(self, name):

        URI = 'api/juniper/sd/service-management/services?filter=(global eq \'' + name + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.service-management.services+xml;version=1;q=0.01'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        service_name = 0
        service_id = 0

        if 'Any' in name:

            for neighbor in xmlRoot.findall('service'):

                if 'Any' in neighbor.find('name').text:
                    service_name = service_name
                    service_id = neighbor.find('id').text
        else:

            for neighbor in xmlRoot.findall('service'):
                service_name = neighbor.find('name').text
                service_id = neighbor.find('id').text

        service_data = {'name': service_name, 'id': service_id}

        return service_data

    def get_device_by_name(self, name):

        URI = 'api/juniper/sd/device-management/devices?filter=(name eq \'' + name + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.device-management.devices+xml;version=1;q=0.0'}

        xmlData = self.get(URI, HEADER)

        if xmlData.status_code == 404:

            self.logger.info('PROVSPACE: Failure in retrieving device information')
            return c.SRC_RESPONSE_FAILURE

        else:

            xmlRoot = ET.fromstring(xmlData.text)

            device_name = 0
            device_id = 0
            moid = 0

            for neighbor in xmlRoot.findall('device'):
                device_name = neighbor.find('name').text
                device_id = neighbor.find('id').text
                moid = neighbor.find('moid').text

            device_data = {'name': device_name, 'id': device_id, 'moid': moid}

            return device_data

    def get_rule_profile_by_name(self, name):

        URI = 'api/juniper/sd/fwpolicy-management/policy-profiles?filter=(name eq \'' + name + '\')'
        HEADER = {'Accept': 'application/vnd.juniper.sd.fwpolicy-management.policy-profiles+xml;version=1;q=0.01'}

        xmlData = self.get(URI, HEADER)
        xmlRoot = ET.fromstring(xmlData.text)

        profile_name = 0
        profile_id = 0

        for neighbor in xmlRoot.findall('policy-profile'):
            profile_name = neighbor.find('name').text
            profile_id = neighbor.find('id').text

        profile_data = {'name': profile_name, 'id': profile_id}

        return profile_data

    def get_modeled_device_instance_id(self, model):
        """

        :param model:
        :return:
        """

        URI = 'api/space/device-management/modeled-device-management/modeled-instances'
        HEADER = {
            'Accept': 'application/vnd.net.juniper.space.device-management.modeled-device-management.modeled-instances+xml;version=1;q=0.01'}

        response = self.get(URI, HEADER)

        xmlRoot = ET.fromstring(response.text)

        for neighbor in xmlRoot.findall('modeled-instance'):

            instance_name = neighbor.find('name').text
            instance_id = neighbor.find('id').text

            # If instance_name is equal to model we want to add, we collect information and return them
            if instance_name == model:
                result = dict()
                result['name'] = instance_name
                result['id'] = instance_id
                return result

            else:
                self.logger.info('PROVSPACE: No instance found for model type %s', model)
                return 'False'

        return 'False'

    def publish_policy(self, body):

        URI = 'api/juniper/sd/fwpolicy-management/publish'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.publish+xml;version=1;charset=UTF-8'}
        self.post(URI, HEADER, body)

    def publish_and_update_policy(self, body):

        URI = 'api/juniper/sd/fwpolicy-management/publish?update=true'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.publish+xml;version=1;charset=UTF-8'}
        self.post(URI, HEADER, body)

    def delete_fw_policy_by_id(self, pid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + pid
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.modify-rules+xml;version=1;charset=UTF-8'}

        self.delete(URI, HEADER)

    def delete_fw_rule(self, body):

        URI = 'api/juniper/sd/fwpolicy-management/modify-rules'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.modify-rules+xml;version=1;charset=UTF-8'}

        self.post(URI, HEADER, body)

    def delete_address_object_by_id(self, id):

        URI = 'api/juniper/sd/address-management/addresses/' + id
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.address-management.delete-address-response+xml;version=1;q=0.01'}
        self.delete(URI, HEADER)

    def delete_service_object_by_id(self, id):

        URI = 'api/juniper/sd/service-management/services/' + id
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.service-management.service+xml;version=1;charset=UTF-8'}

        self.delete(URI, HEADER)

    def discover_device(self, body):

        URI = 'api/space/device-management/discover-devices?queue=https://' + c.conf.JUNOSSPACE.Ip + '/api/hornet-q/queues/jms.queue.yaptQueue'
        HEADER = {
            'Content-Type': 'application/vnd.net.juniper.space.device-management.discover-devices+xml;version=2;charset=UTF-8'}

        self.post(URI, HEADER, body)

    def assign_device(self, body, pid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + pid + '/assign-devices/'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.fwpolicy-management.assign-devices+xml;version=1;charset=UTF-8',
            'Accept': 'application/vnd.juniper.sd.device-management.device+xml;version=1;q=0.01'}

        self.post(URI, HEADER, body)

    def lock_fw_policy(self, pid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + pid + '/lock'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.lock-management.lock+xml;version=1;charset=UTF-8'}

        response = self.post(URI, HEADER, "")

        return response

    def unlock_fw_policy(self, pid):

        URI = 'api/juniper/sd/fwpolicy-management/firewall-policies/' + pid + '/unlock'
        HEADER = {'Content-Type': 'application/vnd.juniper.sd.lock-management.lock+xml;version=1;charset=UTF-8'}

        self.post(URI, HEADER, "")

    def createIPSecVPN(self, body):
        URI = 'api/juniper/sd/vpn-management/ipsec-vpns/create-vpn'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.vpn-management.ipsec-vpns.create-vpn+xml;version=2;charset=UTF-8'}

        self.post(URI, HEADER, body)

    def modifyIPSecVPN(self, body):
        URI = 'api/juniper/sd/vpn-management/ipsec-vpns/modify-vpn'
        HEADER = {
            'Content-Type': 'application/vnd.juniper.sd.vpn-management.ipsec-vpns.modify-tunnels+xml;version=2;charset=UTF-8'}

        self.post(URI, HEADER, body)

    def discover_by_space(self, sample_device=None, shared=None):

        with c.lrr_lock:

            c.lrr_counter += 1

        queue = 'yaptDiscover' + str(c.lrr_counter)
        resp = self.create_hornet_queue(queue)

        if resp:

            self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                  logmsg.DISCOVERY_INIT.format(sample_device.deviceSerial)))

            URI = 'api/space/device-management/discover-devices?queue=https://{0}/api/hornet-q/queues/jms.queue.{1}'.format(
                c.conf.JUNOSSPACE.Ip, queue)
            HEADER = {
                'Content-Type': 'application/vnd.net.juniper.space.device-management.discover-devices+xml;version=2;charset=UTF-8'}

            template = Template(open(c.conf.JUNOSSPACE.TemplateDir + '/discoverDevice.j2').read())
            BODY = template.render(ip_address=sample_device.deviceIP, user=c.conf.COMMON.DeviceUsr,
                                   password=Tools.get_password(c.YAPT_PASSWORD_TYPE_DEVICE))

            response = self.post(URI, HEADER, BODY)
            xmlRoot = ET.fromstring(response.text)
            jobId = xmlRoot.find('id').text
            self.logger.info(
                Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial, logmsg.DISCOVERY_JOB.format(str(jobId))))
            URI = 'api/hornet-q/queues/jms.queue.{0}'.format(queue)
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
                        self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                              logmsg.DISCOVERY_STATE.format(
                                                                  'Waiting for Junos Space response')))

                    elif response.status_code == 200:

                        xmlRoot = ET.fromstring(response.text)
                        taskId = xmlRoot.find('taskId').text

                        if jobId == taskId:

                            state = xmlRoot.findall("./state")

                            if state[0].text == 'INPROGRESS':
                                self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                      logmsg.DISCOVERY_STATE.format(state[0].text)))

                            elif state[0].text == 'DONE':
                                self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                      logmsg.DISCOVERY_STATE.format(state[0].text)))

                                self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                      logmsg.DISCOVERY_CLENUP.format(
                                                                          sample_device.deviceSerial)))

                                URI = 'api/hornet-q/queues/jms.queue.' + queue
                                HEADER = ''

                                # Todo: Check response code in response is 204 --> OK
                                # Todo: If not 204 what todo?
                                response = self.delete(URI, HEADER)

                                if c.lrr_counter > 0:
                                    with c.lrr_lock:
                                        c.lrr_counter -= 1

                                summary = xmlRoot.find('summary').text

                                self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                      logmsg.DISCOVERY_OK_SUM.format(
                                                                          sample_device.deviceSerial,
                                                                          summary)))
                                pattern = r'Job was cancelled by user\s.*'

                                regex = re.compile(pattern, re.MULTILINE)
                                result = re.findall(regex, summary)

                                if result:
                                    self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                          logmsg.DISCOVERY_JOB_CANCELED))
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

                                    if result[c.SPACE_DISCOVERY_NOAM] != 0:
                                        self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                              logmsg.DISCOVERY_STATE.format(
                                                                                  'Already managed')))
                                        return c.TASK_STATE_DONE
                                    elif result[c.SPACE_DISCOVERY_NOADF] != 0:
                                        sample_device.deviceTasks.taskState['Discovery'] = 'Failed'
                                        self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                              logmsg.DISCOVERY_STATE.format(
                                                                                  'Failed')))
                                        return c.TASK_STATE_FAILED
                                    elif result[c.SPACE_DISCOVERY_NODS] != 0:
                                        self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                              logmsg.DISCOVERY_STATE.format(
                                                                                  'Succeeded')))
                                        return c.TASK_STATE_DONE
                                    elif result[c.SPACE_DISCOVERY_NOS] != 0:
                                        self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                              logmsg.DISCOVERY_STATE.format(
                                                                                  'Skipped')))
                                        return c.TASK_STATE_DONE
                                    break

                            else:
                                self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                                      logmsg.DISCOVERY_UNKOWN_STATE.format(state[0].text)))
                                return c.TASK_STATE_FAILED
                    else:
                        self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                              logmsg.DISCOVERY_UNKOWN_CODE.format(response.status_code)))
                        return c.TASK_STATE_FAILED

                else:
                    self.logger.info(Tools.create_log_msg(logmsg.SPACE, sample_device.deviceSerial,
                                                          logmsg.DISCOVERY_UNKOWN_CODE.format(response.status_code)))
                    return c.TASK_STATE_FAILED
        else:
            return c.TASK_STATE_FAILED

    def discover_by_configlet(self, sample_device=None, shared=None):

        if sample_device.deviceConnection.connected:

            self.logger.info('PROVCONFIGLET-[%s]: Start connection provisioning process for device: %s',
                             sample_device.deviceIP,
                             sample_device.deviceIP)

            grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=sample_device.deviceGroupData)

            sample_device.deviceTasks.taskState['Discovery'] = 'Copy configlet'

            configlet_dir = grp_cfg.TASKS.Provision.Discovery.ConnectionConfigletDir
            configlet_template_file = configlet_dir + sample_device.deviceModel + \
                                      "/connectionConfiglet.j2"
            configlet_vars_file = configlet_dir + sample_device.deviceModel + \
                                  "/connectionConfigletVars.yml"
            self.logger.info('PROVCONFIGLET-[%s]: Configlet file to be used: %s', sample_device.deviceIP,
                             configlet_template_file)

            datavars = yaml.load(open(configlet_vars_file).read())
            template = Template(open(configlet_template_file).read())

            try:

                sample_device.deviceConnection.cu.lock()

            except LockError as err:

                self.logger.info("PROVCONFIGLET-[%s]: Unable to lock configuration: %s", sample_device.deviceIP,
                                 err.message)
                sample_device.deviceTasks.taskState['Discovery'] = 'Error: Unable to lock configuration'
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                return

            try:
                sample_device.deviceConnection.cu.load(template_path=template, template_vars=datavars, merge=True,
                                                       overwrite=False,
                                                       format='text')

            except ValueError as err:
                self.logger.info(err.message)
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE

            except (ConfigLoadError, Exception) as err:

                self.logger.info("PROVCONFIGLET-[%s]: Unable to load configuration changes: %s",
                                 sample_device.deviceIP,
                                 err.message)
                self.logger.info('PROVCONFIGLET-[%s]: Unlocking the configuration', sample_device.deviceIP)
                sample_device.deviceTasks.taskState['Discovery'] = 'Unable to load configuration changes'
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE

                try:

                    sample_device.deviceConnection.cu.unlock()

                except UnlockError:

                    self.logger.info("PROVCONFIGLET-[%s]: Error --> Unable to unlock configuration",
                                     sample_device.deviceIP)
                    sample_device.deviceTasks.taskState[
                        'Discovery'] = 'Error: Unable to unlock configuration'
                    shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                return

            self.logger.info('PROVCONFIGLET-[%s]: Committing configuration', sample_device.deviceIP)
            sample_device.deviceTasks.taskState['Discovery'] = 'Committing configuration'

            try:

                sample_device.deviceConnection.cu.commit()

            except (CommitError, ConnectClosedError, RpcTimeoutError):

                self.logger.info("PROVCONFIGLET-[%s]: Error --> Unable to commit configuration",
                                 sample_device.deviceIP)
                self.logger.info("PROVCONFIGLET-[%s]: Unlocking the configuration", sample_device.deviceIP)
                sample_device.deviceTasks.taskState['Discovery'] = 'Error: Unable to commit configuration'
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE

                try:

                    sample_device.deviceConnection.cu.unlock()

                except UnlockError:

                    self.logger.info("PROVCONFIGLET-[%s]: Error --> Unable to unlock configuration",
                                     sample_device.deviceIP)
                    sample_device.deviceTasks.taskState[
                        'Discovery'] = 'Error: Unable to unlock configuration'
                    shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
                return

            self.logger.info('PROVCONFIGLET-[%s]: Unlocking the configuration', sample_device.deviceIP)
            sample_device.deviceTasks.taskState['Discovery'] = 'Unlocking the configuration'

            try:
                sample_device.deviceConnection.cu.unlock()

            except UnlockError as err:

                self.logger.info('PROVCONFIGLET-[%s]: Unable to unlock configuration: %s', sample_device.deviceIP,
                                 err.message)
                sample_device.deviceTasks.taskState['Discovery'] = 'Error: Unable to unlock configuration'
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE

            self.logger.info('PROVCONFIGLET-[%s]: Configuration template: %s committed on device: %s',
                             sample_device.deviceIP,
                             template, sample_device.deviceIP)
            sample_device.deviceTasks.taskState['Discovery'] = Tools.TASK_STATE_DONE
            shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_DONE

        else:
            self.logger.info('PROVCONFIGLET-[%s]: No connection to device %s', sample_device.deviceIP,
                             sample_device.deviceIP)
            shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE

        sample_device.deviceTasks.taskState['Discovery'] = 'Add new device instance'
        instance_id = self.get_modeled_device_instance_id(sample_device.deviceModel)

        if instance_id != 'False':

            response = self.add_modeled_device_instance(instance_id['id'], 1)

            if response == c.SRC_RESPONSE_FAILURE:
                sample_device.deviceTasks.taskState['Discovery'] = 'Error adding device'
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE

            else:

                sample_device.deviceTasks.taskState['Discovery'] = Tools.TASK_STATE_DONE
                shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_DONE

        else:
            self.logger.info('PROVCONFIGLET-[%s]: Instance <%s> not found',
                             sample_device.deviceIP, sample_device.deviceModel)
            sample_device.deviceTasks.taskState['Discovery'] = 'Instance <{0}> not found'.format(
                sample_device.deviceModel)
            shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
