# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

from lib.tasks.task import Task


class MyOwnTask(Task):
    def __init__(self, task_name=None, sample_device=None, shared=None, task_type=None):
        super(MyOwnTask, self).__init__(task_name=task_name, sample_device=sample_device, shared=shared,
                                        task_type=task_type)
        self.logger.debug('Subclass: %s', issubclass(MyOwnTask, Task))
        self.logger.debug('Instance: %s', isinstance(MyOwnTask, Task))

    def pre_run_task(self):
        pass

    def run_task(self):
        self.logger.info("PROVMYOWN-[%s]: Executed MyOwnTask")

    def post_run_task(self):
        pass
