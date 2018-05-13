# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


class AMQPMessage(object):

    # ------------------------------------------------------------------------
    # property: message_type
    # ------------------------------------------------------------------------

    @property
    def message_type(self):
        """
        :returns: message_type defines action to be done when received through message bus
        """
        return self.__message_type

    # ------------------------------------------------------------------------
    # property: data
    # ------------------------------------------------------------------------

    @property
    def payload(self):
        """
        :returns: data contains message payload
        """
        return self.__payload

    @payload.setter
    def payload(self, value):
        self.__payload = value

    # ------------------------------------------------------------------------
    # property: source
    # ------------------------------------------------------------------------

    @property
    def source(self):
        """
        :returns: the message sender
        """
        return self.__source

    def __init__(self, message_type=None, payload=None, source=None):
        """

        :param message_type:
        :param message:
        :param source:
        """

        self.__message_type = message_type
        self.__payload = payload
        self.__source = source
