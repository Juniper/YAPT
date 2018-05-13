# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import abc
import requests
from requests import Request, Session
from lib.logmsg import LogSpace as logmsg
import lib.constants as c
from lib.tools import Tools

requests.packages.urllib3.disable_warnings()


class SpaceRestConnector(object):
    def __init__(self, space_ip=None, space_user=None, space_password=None):

        self.logger = c.logger
        self.__space_ip = space_ip
        self.__space_user = space_user
        self.__space_password = space_password
        self.__space_session = Session()
        self.__space_session.auth = (self.__space_user, self.__space_password)
        self.__rest_timeout = c.conf.JUNOSSPACE.RestTimeout

    def create_hornet_queue(self, queue):

        URI = 'api/hornet-q/queues'
        HEADER = {'Content-Type': 'application/hornetq.jms.queue+xml'}
        BODY = '<queue name="{0}"><durable>false</durable></queue>'.format(queue)
        response = self.post(URI, HEADER, BODY)

        # Check status code to ensure Queue is present on space server
        if response is not None:
            if response.status_code == 201:
                self.logger.info(Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_Q_CREATED.format(queue)))
                return True
            elif response.status_code == 412:
                self.logger.info(Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_Q_ALREADY.format(queue)))
                return True
            else:
                self.logger.info(Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_Q_FAILED.format(queue)))

            return False
        else:
            return False

    def post(self, uri, header, body):

        space_uri = "{0}{1}".format("https://{0}/".format(self.__space_ip), uri)
        req = Request('POST', url=space_uri, data=body, headers=header)
        prepped = self.__space_session.prepare_request(req)

        try:

            response = self.__space_session.send(prepped, stream=None, verify=False, proxies=None, cert=None,
                                                 timeout=10.0)
            self.logger.debug(
                "RESTLIB: ##########################################---POST-BEGIN---##########################################\n")
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: URL: %s', str(space_uri))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Cookie: %s', str(self.__space_session.cookies))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Request Header: %s', str(req.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Header: %s', str(response.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Code: %s', str(response.status_code))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Content: %s', str(response.content))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Body Content: ')
            # Todo: Print body info to logger
            self.logger.debug(body)
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------\n")
            self.logger.debug(
                "RESTLIB: ##########################################---POST-END---############################################\n")

            return response

        except requests.exceptions.RequestException as err:
            self.logger.info(Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_CONN_NOK.format(self.__space_ip, err)))

    def get(self, uri, header):

        space_uri = "{0}{1}".format("https://{0}/".format(self.__space_ip), uri)
        req = Request('GET', url=space_uri, headers=header)
        prepped = self.__space_session.prepare_request(req)

        try:
            response = self.__space_session.send(prepped, stream=None, verify=False, proxies=None, cert=None,
                                                 timeout=10.0)

            self.logger.debug(
                "RESTLIB: ##########################################---GET-BEGIN---##########################################\n")
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: URL: %s', str(space_uri))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Cookie: %s', str(self.__space_session.cookies))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Request Header: %s', str(req.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Header: %s', str(response.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Code: %s', str(response.status_code))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Content: %s', str(response.content))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug(
                "RESTLIB: ##########################################---GET-END---############################################\n")

            return response

        except requests.exceptions.RequestException as err:
            self.logger.info(
                Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_CONN_NOK.format(self.__space_ip, err)))

    def delete(self, uri, header):

        space_uri = "{0}{1}".format("https://{0}/".format(self.__space_ip), uri)
        req = Request('DELETE', url=space_uri, headers=header)
        prepped = self.__space_session.prepare_request(req)

        try:

            response = self.__space_session.send(prepped, stream=None, verify=False, proxies=None, cert=None,
                                                 timeout=10.0)

            self.logger.debug(
                "RESTLIB: ##########################################---DELETE-BEGIN---##########################################\n")
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: URL: %s', str(space_uri))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Cookie: %s', str(self.__space_session.cookies))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Request Header: %s', str(req.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Header: %s', str(response.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Code: %s', str(response.status_code))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Content: %s', str(response.content))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug(
                "RESTLIB: ##########################################---DELETE-END---############################################\n")

            return response

        except requests.exceptions.RequestException as err:
            self.logger.info(
                Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_CONN_NOK.format(self.__space_ip, err)))

    def head(self, uri, header, body):

        space_uri = "{0}{1}".format("https://{0}/".format(self.__space_ip), uri)
        req = Request('HEAD', url=space_uri, data=body, headers=header)
        prepped = self.__space_session.prepare_request(req)

        try:

            response = self.__space_session.send(prepped, stream=None, verify=False, proxies=None, cert=None,
                                                 timeout=10.0)

            self.logger.debug(
                "RESTLIB: ##########################################---HEAD-BEGIN---##########################################\n")
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: URL: %s', str(space_uri))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Cookie: %s', str(self.__space_session.cookies))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Request Header: %s', str(req.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Header: %s', str(response.headers))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Code: %s', str(response.status_code))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Response Content: %s', str(response.content))
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------")
            self.logger.debug('RESTLIB: Body Content: ')
            # Todo: log to logger
            self.logger.debug(body)
            self.logger.debug(
                "RESTLIB: ----------------------------------------------------------------------------------------------\n")
            self.logger.debug(
                "RESTLIB: ##########################################---HEAD-END---############################################\n")

            return response

        except requests.exceptions.RequestException as err:
            self.logger.info(
                Tools.create_log_msg(logmsg.SPACE, None, logmsg.SPACEPLG_CONN_NOK.format(self.__space_ip, err)))

    @abc.abstractmethod
    def discover_by_space(self, sample_device=None, shared=None):
        raise NotImplementedError()

    @abc.abstractmethod
    def discover_by_configlet(self, sample_device=None, shared=None):
        raise NotImplementedError()

    def end_session(self):
        self.__space_session.close()
