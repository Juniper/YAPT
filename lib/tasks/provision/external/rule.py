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
import time

import yaml
from jinja2 import Template

from lib.logmsg import LogCommon
from lib.logmsg import LogRuleTask as logmsg
from lib.tasks.task import Task
import lib.constants as c
from lib.tools import Tools


class RuleTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_PROVISION
    TASK_VERSION = 1.0

    def __init__(self, sample_device, shared):

        super(RuleTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(RuleTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):

        self.logger.info('PROVSPACE: Start Junos Space policy rule add process for device: %s',
                         self.sample_device.deviceIP)
        self.sample_device.deviceTasks.taskState[self.task_name] = 'Get Policy'
        policy_data = c.SRC.get_fw_policy_by_name(self.sample_device.deviceName)

        if policy_data == c.SRC_RESPONSE_FAILURE:

            self.sample_device.deviceTasks.taskState[self.task_name] = c.SRC_RESPONSE_FAILURE

        else:

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Get src address'
            address_data_src = c.SRC.get_address_by_name('Any')

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Get dst address'
            address_data_dst = c.SRC.get_address_by_name('Any')

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Get service'
            service_data = c.SRC.get_service_by_name('Any')

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Get Profile'
            profile_data = c.SRC.get_rule_profile_by_name('All Logging Enabled')

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Get Member'
            policy_data = c.SRC.get_fw_policy_member_by_id(policy_data['pid'], policy_data['mid'])

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Building Rule'

            isNotSourceIdentity = '<source-identities/>'

            try:

                with open(c.conf.JUNOSSPACE.TemplateDir + self.grp_cfg.TASKS.Provision.Rule.RuleTemplate,
                          'r') as file:
                    template = Template(file)

                with open(c.conf.JUNOSSPACE.TemplateDir + self.grp_cfg.TASKS.Provision.Rule.RuleTemplateVars,
                          'r') as file:

                    ruleVars = yaml.load(file)

            except IOError as ioe:
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.RULE_FILE_NOK.format(ioe.filename, ioe.message)))
                self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_FAILED
                self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE
                return

            body = template.render(ruleVars, version=policy_data['version'], pid=policy_data['pid'],
                                   gid=policy_data['gid'], gpname=policy_data['name'],
                                   srcAddrName=address_data_src['name'], srcAddrId=address_data_src['id'],
                                   identities=isNotSourceIdentity, dstAddrName=address_data_dst['name'],
                                   dstAddrId=address_data_dst['id'], serviceId=service_data['id'],
                                   serviceName=service_data['name'], rpname=profile_data['name'],
                                   rpid=profile_data['id'])

            time.sleep(c.conf.JUNOSSPACE.RestTimeout)
            self.sample_device.deviceTasks.taskState[self.task_name] = 'Lock Policy'
            response = c.SRC.lock_fw_policy(policy_data['pid'])

            if response.status_code == 500:
                self.logger.info(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                                      logmsg.RULE_INIT_NOK.format(response.status_code, response.text)))
                self.sample_device.deviceTasks.taskState[self.task_name] = c.SRC_RESPONSE_FAILURE
                self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_FAILURE

            else:

                time.sleep(c.conf.JUNOSSPACE.RestTimeout)
                self.sample_device.deviceTasks.taskState[self.task_name] = 'Adding Rule'
                c.SRC.add_fw_rule(body)

                time.sleep(c.conf.JUNOSSPACE.RestTimeout)
                self.sample_device.deviceTasks.taskState[self.task_name] = 'Unlock Policy'
                c.SRC.unlock_fw_policy(policy_data['pid'])

                time.sleep(c.conf.JUNOSSPACE.RestTimeout)
                self.sample_device.deviceTasks.taskState[self.task_name] = c.TASK_STATE_DONE
                self.shared[c.TASK_SHARED_STATE] = c.TASK_STATE_RESULT_DONE

    def post_run_task(self):
        pass
