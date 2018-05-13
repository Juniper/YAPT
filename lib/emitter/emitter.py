# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import abc
import lib.constants as c


class Emitter(object):

    def __init__(self):
        self.logger = c.logger

    @abc.abstractmethod
    def emit(self, task_name=None, task_state=None, sample_device=None, grp_cfg=None, shared=None, message=None,
             level=c.LOGGER_LEVEL_INFO):
        raise NotImplementedError()
