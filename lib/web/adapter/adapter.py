# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import abc

from ws4py.client.threadedclient import WebSocketClient


class UiAdapter(WebSocketClient):

    @abc.abstractmethod
    def prepare_device_task_data(self, sample_device=None, action=None, task_name=None):
        raise NotImplementedError()