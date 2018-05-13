# Copyright (c) 1999-2018, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar
#

import lib.constants as c

#from jnpr.jsnapy import SnapAdmin
from lib.logmsg import LogCommon
from lib.tasks.task import Task
from lib.tools import Tools


class JsnapyTask(Task):
    CHECK_SCHEMA = False
    TASK_TYPE = c.TASK_TYPE_VERIFICATION
    TASK_VERSION = 1.0

    def __init__(self, sample_device=None, shared=None):
        super(JsnapyTask, self).__init__(sample_device=sample_device, shared=shared)
        self.logger.debug(Tools.create_log_msg(self.task_name, self.sample_device.deviceSerial,
                                               LogCommon.IS_SUBCLASS.format(self.task_name,
                                                                            issubclass(JsnapyTask, Task))))

    def pre_run_task(self):
        pass

    def run_task(self):
        pass

        '''
        js = SnapAdmin()
        self.logger.info('VERIFYJSNAPY-[%s]: Starting Verfification with JSNAPY Task')
        snapvalue = js.snapcheck({'tests': dev_grp.TASKS.Verification.Jsnap.Tests}, "PRE",
                                 dev=self.sample_device.deviceConnection, folder='conf/jsnapy')

        result = 'Passed'

        for snapcheck in snapvalue:
        
            #Todo: disable Jsnapy's own logger
        
            self.logger.info('VERIFYJSNAPY-[%s]: -----------snapcheck----------')
            self.logger.info('VERIFYJSNAPY-[%s]: Tested on device: %s', self.sample_device.deviceIP, snapcheck.device)
            self.logger.info('VERIFYJSNAPY-[%s]: Final result %s ', self.sample_device.deviceIP, snapcheck.result)
            self.logger.info('VERIFYJSNAPY-[%s]: Total passed:  %s ', self.sample_device.deviceIP, snapcheck.no_passed)
            self.logger.info('VERIFYJSNAPY-[%s]: Total Failed:  %s ', self.sample_device.deviceIP, snapcheck.no_failed)
            self.logger.info('VERIFYJSNAPY-[%s]: Test Results: %s', self.sample_device.deviceIP, snapcheck.test_results)
            
        if snapcheck.result == 'Failed':
            result = 'Failed'

    if result == 'Passed':
        self.logger.info('VERIFYJSNAPY-[%s]: Verfification task JSNAPY passed')
        self.sample_device.deviceVerificationTasks.taskState['Jsnapy'] = Tools.TASK_STATE_DONE
        self.shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_DONE
    else:
        self.logger.info('VERIFYJSNAPY-[%s]: Verfification task JSNAPY failed')
        self.sample_device.deviceVerificationTasks.taskState['Jsnapy'] = Tools.TASK_STATE_FAILURE
        self.shared[Tools.TASK_SHARED_STATE] = Tools.TASK_STATE_RESULT_FAILURE
        '''

    def post_run_task(self):
        pass
