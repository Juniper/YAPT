# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#

import time
import json
import threading

import cherrypy
import jsonpickle
import ruamel.yaml
import six
from cherrypy._cpserver import Server
from ruamel.yaml.util import load_yaml_guess_indent

from lib.amqp.amqpmessage import AMQPMessage
import lib.constants as c
from lib.processor import BackendClientProcessor
from ws4py.client.threadedclient import WebSocketClient

"""
# First draft YAPT Rest API. Lot of stuff still missing
# - Authentication
# - Response header handling
# - Exception Handling
# - Encryption
"""

auth_file_lock = threading.Lock()


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


def yaml_processor(entity):
    """
    Unserialize raw POST data in YAML format to a Python data structure.
    :param entity: raw POST data
    """

    body = entity.fp.read()

    try:
        _datavars, ind, bsi = load_yaml_guess_indent(body)
        cherrypy.serving.request.unserialized_data = _datavars

    except ValueError:
        raise cherrypy.HTTPError(400, 'Invalid YAML document')

    cherrypy.serving.request.raw_body = body


def text_processor(entity):
    if six.PY2:
        body = entity.fp.read()
    else:
        contents = six.StringIO()
        body = entity.fp.read(fp_out=contents)
        contents.seek(0)
        body = contents.read()

    try:
        cherrypy.serving.request.unserialized_data = body
    except ValueError:
        cherrypy.serving.request.unserialized_data = body

    cherrypy.serving.request.raw_body = body


@cherrypy.tools.register('before_request_body')
def yaml_tool():
    """
    Unserialize POST data of a specified Content-Type.

    Using custom processor to directly process yaml data.

    :raises HTTPError: if the request contains a Content-Type that we do not
    have a processor for
    """

    ct_in_map = {'application/x-yaml': yaml_processor, 'text/plain': text_processor}

    # Do not process the body for POST requests that have specified no content
    # or have not specified Content-Length

    if cherrypy.request.method.upper() == 'POST' and cherrypy.request.headers.get('Content-Length', '0') == '0':
        cherrypy.request.process_request_body = False
        cherrypy.request.unserialized_data = None

    cherrypy.request.body.processors.clear()
    cherrypy.request.body.default_proc = cherrypy.HTTPError(406, 'Content type not supported')
    cherrypy.request.body.processors = ct_in_map


class RestBase(object):
    def __init__(self, args=None):
        self._backendp = args


class Device(RestBase):
    exposed = True

    @cherrypy.tools.yaml_tool()
    def POST(self, sn=None):
        new_device = cherrypy.serving.request.unserialized_data

        with open(c.conf.YAPT.DeviceConfDataDir + sn + '.yml', 'w') as fp:
            ruamel.yaml.dump(new_device, fp, Dumper=ruamel.yaml.RoundTripDumper)

        return 'successfully added device config %s to data store' % sn

    def GET(self, sn=None):

        if sn == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEV_GET_ALL, payload=sn,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)
            devices = list()

            for serial, data in response.payload.iteritems():
                sample_device = data['data'].device_to_json()
                devices.append(sample_device)

            return '[{0}]'.format(', '.join(devices))

        else:

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEV_GET_BY_SN, payload=sn,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)


class Template(RestBase):
    exposed = True

    @cherrypy.tools.yaml_tool()
    def POST(self, name=None):
        new_template = cherrypy.serving.request.unserialized_data

        # with open(Tools.conf.TASKS.Configuration.DeviceConfTemplateDir + name, 'w') as fp:
        #    fp.write(new_template)

        return 'adding template'

    def GET(self):
        return 'getting template'


class Group(RestBase):
    exposed = True

    @cherrypy.tools.yaml_tool()
    def POST(self, action=None, name=None, descr=None):

        if action == 'add':
            new_device = cherrypy.serving.request.unserialized_data

            try:

                with open(c.conf.SOURCE.Local.DeviceGrpFilesDir + name + '.yml', 'w') as fp:
                    ruamel.yaml.dump(new_device, fp, Dumper=ruamel.yaml.RoundTripDumper)

            except Exception as e:
                return str(e)

            payload = {'groupName': name, 'groupConfig': new_device, 'groupDescr': descr}
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_ADD, payload=payload,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)
            response = json.dumps(response.payload)

            if response:
                return 'Successfully added group config <%s> to data store' % name
            else:
                return 'Failed to add group <%s> to datastore' % name

        else:
            return 'Action not defined'

    def GET(self, action=None, name=None):

        if action == 'all':
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_ALL, payload=action,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)

        elif action == 'config':

            with open(c.conf.SOURCE.Local.DeviceGrpFilesDir + name + '.yml', 'r') as stream:
                content = stream.read()
                return content

        else:

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)


class Authenticate(RestBase):
    exposed = True

    def POST(self, sn=None):
        with auth_file_lock:
            with open(c.conf.SERVICES.Phs.DeviceAuthFile, 'a') as auth_file:
                auth_file.write(sn + '\n')
                return 'Successfully added device <%s> to trust store' % sn


class Site(RestBase):
    exposed = True

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, action=None):

        if action == 'add':

            input_json = cherrypy.request.json
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_ADD, payload=input_json,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response:
                return 'Successfully added site <%s> to datastore' % input_json['siteId']
            else:
                return 'Failed to add site <%s> to datastore' % input_json['siteId']

        else:
            return 'Action not defined'

    def GET(self, siteId=None):

        if siteId == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_GET_ALL, payload=siteId,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)
            response = json.dumps(response.payload)

            return response

        else:

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_GET_BY_ID, payload=siteId,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)
            response = json.dumps(response.payload)

            return response


class Asset(RestBase):
    exposed = True

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, action=None):

        if action == 'add':

            input_json = cherrypy.request.json
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_ADD, payload=input_json,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response:
                return 'Successfully add asset <{0}>'.format(input_json['assetConfigId'])
            else:
                return 'Failed to add asset <{0}>'.format(input_json['assetConfigId'])

        elif action == 'update':

            input_json = cherrypy.request.json
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_UPDATE, payload=input_json,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return 'Successfully mapped asset <{0}> to asset config <{1}>'.format(input_json['assetSerial'],
                                                                                  input_json['assetConfigId'])

        else:
            return 'Action not defined'

    @cherrypy.tools.json_out()
    def GET(self, action=None, assetSerial=None):

        if action == 'get_by_serial':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_GET, payload=assetSerial,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return {"assetConfigId": response.payload}

        else:
            return 'Action not defined'


class Logs(RestBase):
    exposed = True

    def GET(self, ):
        url = 'ws://{0}:{1}/yapt/ws?clientname={2}'.format(c.conf.YAPT.WebUiAddress,
                                                           str(c.conf.YAPT.WebUiPort), c.conf.YAPT.WebUiPlugin)
        wsc = WebSocketClient(url=url)
        wsc.connect()

        with open('./logs/info.log', 'r') as stream:
            log_data = stream.read()

        if log_data:
            wsc.send(payload=json.dumps({'action': c.UI_ACTION_INIT_LOG_VIEWER, 'data': log_data}))

        wsc.close()


class YaptRestApi(object):
    """
    YAPT REST API mapping
    """

    url_map = {'device': Device, 'template': Template, 'group': Group, 'authenticate': Authenticate,
               'site': Site, 'asset': Asset, 'logs': Logs}

    def _setattr_url_map(self, args=None):
        """
        Set an attribute on the local instance for each key/val in url_map
        """

        for url, cls in six.iteritems(self.url_map):
            setattr(self, url, cls(args=args))

    def __init__(self):
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        self._setattr_url_map(args=self._backendp)
        self._host = c.conf.YAPT.WebUiAddress
        self._port = str(c.conf.YAPT.RestApiPort)
        yapt_rest_server = Server()
        yapt_rest_server.socket_host = self._host
        yapt_rest_server.socket_port = int(self._port)
        yapt_rest_server.subscribe()
        cherrypy.tools.cors_tool = cherrypy.Tool('before_request_body', cors_tool, name='cors_tool', priority=50)
        cherrypy.config.update({'log.screen': False,
                                'engine.autoreload.on': False,
                                })
