# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import os
import sys
import cherrypy
import lib.constants as c
import multiprocessing
import datetime

from cherrypy._cpserver import Server
from lib.services.service import Service
from lib.processor import BackendClientProcessor
from lib.amqp.amqpmessage import AMQPMessage
from lib.tools import Tools
from lib.logmsg import Logwebhook as logmsg
from lib.logmsg import LogCommon


def cors_tool():
    req_head = cherrypy.request.headers
    resp_head = cherrypy.response.headers

    resp_head['Access-Control-Allow-Origin'] = req_head.get('Origin', '*')
    resp_head['Access-Control-Expose-Headers'] = 'GET, POST'
    resp_head['Access-Control-Allow-Credentials'] = 'true'

    if cherrypy.request.method == 'OPTIONS':
        ac_method = req_head.get('Access-Control-Request-Method', None)

        allowed_methods = ['GET', 'POST']
        allowed_headers = [
            'Content-Type',
            'X-Auth-Token',
            'X-Requested-With',
        ]

        if ac_method and ac_method in allowed_methods:
            resp_head['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
            resp_head['Access-Control-Allow-Headers'] = ', '.join(allowed_headers)

            resp_head['Connection'] = 'keep-alive'
            resp_head['Access-Control-Max-Age'] = '1400'

        cherrypy.response.body = ''
        cherrypy.response.status = 200
        cherrypy.serving.request.handler = None

        if cherrypy.request.config.get('tools.sessions.on', False):
            cherrypy.session['token'] = True
        return True


class Webhook(Service):

    def __init__(self, normalizer, svc_cfg):
        super(Webhook, self).__init__(normalizer=normalizer, svc_cfg=svc_cfg)
        self._stop_service = multiprocessing.Event()
        self.p = None
        self.logger.debug(Tools.create_log_msg(logmsg.WEBHOOK_SERVICE, None,
                                               LogCommon.IS_SUBCLASS.format(logmsg.WEBHOOK_SERVICE,
                                                                            issubclass(Webhook, Service))))
        self.logger.info(Tools.create_log_msg(logmsg.WEBHOOK_SERVICE, None, logmsg.WEBHOOK_START))

    def start_service(self):
        if self.status == c.SVC_STOPPED or self.status == c.SVC_INIT:
            #multiprocessing.set_start_method('spawn')
            self.p = multiprocessing.Process(target=WebhookInit, args=(self.normalizer, self.svc_cfg))
            self.p.start()
            self.status = c.SVC_STARTED
            return self.status
        else:
            return self.status

    def stop_service(self):

        if self.status == c.SVC_STARTED:

            self.p.terminate()
            self.p.join()
            self.status = c.SVC_STOPPED
            self.logger.info(
                Tools.create_log_msg(logmsg.WEBHOOK_SERVICE, None,
                                     logmsg.WEBHOOK_STOPPED.format(c.conf.SERVICES.Webhook.ServiceBindAddress,
                                                                   c.conf.SERVICES.Webhook.ServiceListenPort)))
            return self.status

        else:
            return self.status

    def restart_service(self):

        if self.status == c.SVC_STOPPED:

            self.start_service()
            return self.status
        else:

            self.stop_service()
            self.start_service()
            return self.status


class WebhookInit(object):

    def __init__(self, normalizer, svc_cfg):
        self.logger = c.logger
        cherrypy.config.update('{0}/{1}'.format(os.getcwd(), c.SVC_WEBHOOK_CONF))

        for module in c.conf.SERVICES.Webhook.Modules:
            handler = getattr(sys.modules[__name__], module + 'WebHookHandler')
            cherrypy.tree.mount(handler(normalizer=normalizer, svc_cfg=svc_cfg),
                                script_name='/' + module.lower(),
                                config='{0}/{1}'.format(os.getcwd(),
                                                        '{0}{1}{2}'.format(c.SVC_WEBHOOK_PATH, module.lower(),
                                                                           '.conf')))
        self._webhook_server = Server()
        self._webhook_server.socket_host = c.conf.SERVICES.Webhook.ServiceBindAddress
        self._webhook_server.socket_port = c.conf.SERVICES.Webhook.ServiceListenPort
        self._webhook_server.subscribe()
        self.logger.info(Tools.create_log_msg(logmsg.WEBHOOK_SERVICE, None,
                                              logmsg.WEBHOOK_LISTEN.format(self._webhook_server.socket_host,
                                                                           self._webhook_server.socket_port)))

        cherrypy.engine.start()
        cherrypy.engine.block()


class GitlabWebHookHandler(object):
    exposed = True

    def __init__(self, normalizer=None, svc_cfg=None):
        self.logger = c.logger
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        cherrypy.tools.cors_tool = cherrypy.Tool('before_request_body', cors_tool, name='cors_tool', priority=50)
        self._normalizer = normalizer
        self._plugin_cfg = svc_cfg

    @cherrypy.tools.json_in()
    def POST(self):
        input_json = cherrypy.request.json

        _data = [_file for commit in input_json['commits'] for _file in commit['modified']]

        for item in _data:

            data = item.rsplit('.', 1)[0]
            self.logger.info(Tools.create_log_msg(logmsg.WEBHOOK_SERVICE, data, logmsg.WEBHOOK_RECEIVED.format(data)))
            _data = self._normalizer.run_normalizer(
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), device=data)

            if _data[0]:

                message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD,
                                      payload=_data[1],
                                      source=c.AMQP_PROCESSOR_SVC)

                self._normalizer.send_message(message=message)


class GithubWebHookHandler(object):

    def __init__(self, normalizer=None, svc_cfg=None):
        self.logger = c.logger
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        cherrypy.tools.cors_tool = cherrypy.Tool('before_request_body', cors_tool, name='cors_tool', priority=50)
        self._source_plugin = normalizer
        self._plugin_cfg = svc_cfg

    @cherrypy.tools.json_in()
    def POST(self):
        input_json = cherrypy.request.json

        _data = [_file for commit in input_json['commits'] for _file in commit['modified']]

        for item in _data:
            print item.rsplit('.', 1)[0]
