# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import json
import os
import random
import threading

import cherrypy
from cherrypy._cpserver import Server
from cherrypy.lib import auth_digest
from cherrypy.process import plugins
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket

from lib.amqp.amqpmessage import AMQPMessage

from lib.processor import ClientProcessor
from lib.logmsg import LogYaptWebUi as logmsg
import lib.constants as c
from lib.tools import Tools
from lib.web.ooba import YaptOoba
from lib.web.rest import YaptRestApi

env = Environment(loader=FileSystemLoader('lib/web/ui'))


class UiInit(object):
    ##############################
    # Start Cherrypy environment #
    ##############################

    def __init__(self):
        self._current_dir = os.path.dirname(os.path.abspath(__file__))

        USERS = {'jon': 'secret'}

        cherrypy.config.update('{0}/{1}'.format(os.getcwd(), c.SVC_UI_CONF))

        if c.conf.YAPT.StartWebUi:

            if c.conf.YAPT.WebUiProxy:
                print '\n\n############## Starting YAPT WebUI at: http://{0}:{1}/yapt/ui ##############\n\n'.format(
                    c.conf.YAPT.WebUiProxyIp, str(
                        str(c.conf.YAPT.WebUiPort)))
            else:
                print '\n\n############## Starting YAPT WebUI at: http://{0}:{1}/yapt/ui ##############\n\n'.format(
                    c.conf.YAPT.WebUiAddress, str(
                        str(c.conf.YAPT.WebUiPort)))

            web = cherrypy.tree.mount(Web(), '/yapt', '{0}/{1}'.format(os.getcwd(), c.SVC_UI_CONF))

            config = {
                '/ui': {
                    'tools.staticdir.root': self._current_dir

                },
                '/ws': {
                    'tools.websocket.handler_cls': WSHandler
                }
            }
            web.merge(config=config)

        cherrypy.tree.mount(YaptRestApi(), '/api', config='{0}/{1}'.format(os.getcwd(), c.SVC_REST_CONF))
        ooba = cherrypy.tree.mount(YaptOoba(), '/ooba', config='{0}/{1}'.format(os.getcwd(), c.SVC_OOBA_CONF))

        config = {
            '/': {
                'tools.staticdir.root': self._current_dir,
            }
        }
        ooba.merge(config)

        #cherrypy.log.error_log.propagate = False
        #cherrypy.log.access_log.propagate = False

        cherrypy.engine.start()
        cherrypy.engine.block()


class AMQP(plugins.SimplePlugin):
    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)
        self.logger = c.logger
        self.amqpCl = ClientProcessor(exchange=c.conf.AMQP.Exchange, routing_key=c.AMQP_PROCESSOR_UI,
                                      queue=c.AMQP_PROCESSOR_UI)

    def start(self):
        self.bus.log('Starting AMQP processing')
        self.bus.subscribe('CPAMQPPlugin', self.send_message_to_amqp)

    start.priority = 78

    def stop(self):
        self.bus.log('Stopping AMQP access')

    def send_message_to_amqp(self, data=None):
        message = AMQPMessage(message_type=data, payload=data, source='CPAMQPPlugin')
        self.amqpCl.send_message(message=message)


class Plugin(WebSocketPlugin):
    def __init__(self, bus):
        WebSocketPlugin.__init__(self, bus)
        self.ws_servers_lock = threading.Lock()
        self.ws_clients_lock = threading.Lock()
        self.ws_servers = dict()
        self.ws_clients = dict()

    def start(self):
        WebSocketPlugin.start(self)
        self.bus.subscribe('add-server', self.add_server)
        self.bus.subscribe('get-server', self.get_server)
        self.bus.subscribe('del-server', self.del_server)
        self.bus.subscribe('add-client', self.add_client)
        self.bus.subscribe('get-client', self.get_client)
        self.bus.subscribe('del-client', self.del_client)
        self.bus.subscribe('check-client', self.check_client_exists)
        self.bus.subscribe('get-clients', self.get_clients)

    def stop(self):
        WebSocketPlugin.stop(self)
        self.bus.unsubscribe('add-server', self.add_server)
        self.bus.unsubscribe('get-server', self.get_server)
        self.bus.unsubscribe('del-server', self.del_server)
        self.bus.unsubscribe('add-client', self.add_client)
        self.bus.unsubscribe('get-client', self.get_client)
        self.bus.unsubscribe('del-client', self.del_client)
        self.bus.unsubscribe('check-client', self.check_client_exists)
        self.bus.unsubscribe('get-clients', self.get_clients)

    def add_server(self, name, websocket):

        self.ws_servers_lock.acquire()
        try:
            self.ws_servers[name] = websocket
        finally:
            self.ws_servers_lock.release()

    def get_server(self, name):
        return self.ws_servers[name]

    def del_server(self, name):

        self.ws_servers_lock.acquire()

        try:
            if name in self.ws_servers:
                del self.ws_servers[name]
            else:
                pass

        finally:
            self.ws_servers_lock.release()

    def add_client(self, name, websocket):

        self.ws_clients_lock.acquire()
        try:
            self.ws_clients[name] = websocket
        finally:
            self.ws_clients_lock.release()

    def get_client(self, name):
        if name in self.ws_clients:
            return self.ws_clients[name]
        else:
            return None

    def del_client(self, name):

        self.ws_clients_lock.acquire()

        try:
            if name in self.ws_clients:
                del self.ws_clients[name]
            else:
                pass

        finally:
            self.ws_clients_lock.release()

    def check_client_exists(self, name):

        if name in self.ws_clients:
            return True
        else:
            return False

    def get_clients(self):
        return self.ws_clients


class WSHandler(WebSocket):
    tmp_client = None

    def opened(self):

        if self.clientname != c.conf.YAPT.WebUiPlugin:

            if cherrypy.engine.publish('check-client', self.clientname)[0]:
                pass
            else:
                cherrypy.engine.publish('add-client', self.clientname, self)
                WSHandler.tmp_client = self.clientname
        else:
            cherrypy.engine.publish('add-server', self.clientname, self)

    def received_message(self, m):

        try:
            _data = json.loads(m.data)

        except ValueError as ve:
            c.logger.info(Tools.create_log_msg(logmsg.WSHDLR, self.clientname, logmsg.WSHDLR_RCVD_DATA_NOK.format(ve)))
            return None

        all_clients = cherrypy.engine.publish('get-clients')

        for _clients in all_clients:
            for _client_name, client_ws in _clients.iteritems():
                if not client_ws.terminated:
                    client_ws.send(m.data)

    def closed(self, code, reason='Going away'):

        if code == 1000:
            pass
        elif code == 1006 and reason == 'Going away':
            cherrypy.engine.publish('del-client', self.clientname)
        else:
            pass


class Web(object):

    def __init__(self):

        self._host = c.conf.YAPT.WebUiAddress
        self._port = int(c.conf.YAPT.WebUiPort)
        self._scheme = 'ws'

        Plugin(cherrypy.engine).subscribe()
        AMQP(cherrypy.engine).subscribe()

        cherrypy.tools.websocket = WebSocketTool()

        yapt_server = Server()
        yapt_server.socket_host = self._host
        yapt_server.socket_port = self._port
        yapt_server.max_request_body_size = 838860800
        yapt_server.subscribe()

    @cherrypy.expose
    def ui(self):

        if c.conf.YAPT.WebUiProxy:
            _host = c.conf.YAPT.WebUiProxyIp
            _port = int(c.conf.YAPT.WebUiProxyPort)
        else:
            _host = self._host
            _port = self._port

        try:

            tmpl = env.get_template(c.conf.YAPT.WebUiIndex)
            index = tmpl.render(devices=list(), scheme=self._scheme, host=_host,
                                port=_port, clientname="Client%d" % random.randint(0, 100),
                                action_update_status=c.UI_ACTION_UPDATE_STATUS,
                                action_add_device=c.UI_ACTION_ADD_DEVICE,
                                action_update_device=c.UI_ACTION_UPDATE_DEVICE,
                                action_update_device_task_state=c.UI_ACTION_UPDATE_TASK_STATE,
                                action_update_device_and_reset_task_state=c.UI_ACTION_UPDATE_DEVICE_AND_RESET_TASK,
                                action_update_log_viewer=c.UI_ACTION_UPDATE_LOG_VIEWER,
                                action_init_log_viewer=c.UI_ACTION_INIT_LOG_VIEWER)

            return index

        except (TemplateNotFound, IOError) as ioe:

            Tools.create_log_msg(self.__class__.__name__, '',
                                 logmsg.WEBUI_FILE_NOK.format(ioe.filename if ioe.filename else ioe))
            return logmsg.WEBUI_FILE_NOK.format(ioe.filename if ioe.filename else ioe)

    @cherrypy.expose
    def ws(self, clientname):
        cherrypy.request.ws_handler.clientname = clientname
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))
