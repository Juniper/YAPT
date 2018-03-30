# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#

import os
import StringIO
import json
import threading

import cherrypy
import jsonpickle
import ruamel.yaml
import six
import lib.constants as c

from lib.pluginfactory import StoragePlgFact
from cherrypy._cpserver import Server
from ruamel.yaml.util import load_yaml_guess_indent
from lib.amqp.amqpmessage import AMQPMessage
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


def escape(string):
    """Returns the given HTML with ampersands, quotes and carets encoded."""
    return string.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'",
                                                                                                                 '&#39;')


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
        self.storageFact = StoragePlgFact()


class Device(RestBase):
    exposed = True

    @cherrypy.tools.yaml_tool()
    def POST(self, action=None, name=None, descr=None, storage=None):

        if action == 'add':

            if name and storage:

                new_device = cherrypy.serving.request.unserialized_data

                payload = {'configSerial': name, 'configDescr': descr,
                           'configConfigSource': storage}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_CFG_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.add_device_config_data()(deviceSerial=name, deviceData=new_device)

                    if status:
                        return json.dumps((response.payload[0], escape(response.payload[1])))

                    else:
                        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_CFG_DEL, payload=name,
                                              source=c.AMQP_PROCESSOR_REST)
                        response = self._backendp.call(message=message)
                        response = jsonpickle.decode(response)

                        if response.payload[0]:
                            return json.dumps((status, escape(msg)))

                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

            else:
                return json.dumps((False, escape('Mandatory value missing')))

        elif action == 'del':

            if name and storage:

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_CFG_DEL, payload=name,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.del_device_config_data(configSerial=name)

                    if status:
                        return json.dumps((status, escape(response.payload[1])))
                    else:
                        return json.dumps((status, escape(msg)))
                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))
            else:
                return json.dumps((False, escape('Device serial or Config Source empty')))
        else:
            return json.dumps((False, escape('Action not defined')))

    def GET(self, action=None, name=None):

        if action == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_GET_ALL, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)
            devices = list()

            for serial, data in response.payload.iteritems():
                sample_device = data['data'].device_to_json()
                devices.append(sample_device)

            return '[{0}]'.format(', '.join(devices))

        elif action == 'cfgall':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_GET_CFG_ALL, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)

        elif action == 'config':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_GET_CFG_BY_SERIAL, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload[0]:

                storageName = response.payload[1]['configConfigSource']
                storage = self.storageFact.init_plugin(plugin_name=storageName)
                status, msg = storage.get_device_config_data(serialnumber=name, isRaw=True)

                return json.dumps((status, msg))

            else:
                return json.dumps((response.payload[0], escape(response.payload[1])))

        else:
            return json.dumps((False, escape('Action not defined')))


class Template(RestBase):
    exposed = True

    def POST(self, action=None, name=None, descr=None, group=None, storage=None):

        if action == 'add':

            if name:

                new_template = cherrypy.request.body.read()
                payload = {'templateName': name, 'templateConfig': new_template, 'templateDescr': descr,
                           'templateDevGrp': group, 'templateConfigSource': storage}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.add_config_template_data(templateName=name, templateData=new_template,
                                                                   groupName=group)

                    return json.dumps((status, msg))
                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

        elif action == 'del':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload[0]:

                groupName = response.payload[1]['templateDevGrp']
                storage = response.payload[1]['templateConfigSource']

                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_DEL, payload=name,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.del_config_template_data(templateName=name, groupName=groupName)

                    if status:
                        return json.dumps((status, escape(response.payload[1])))
                    else:
                        return json.dumps((status, msg))

                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))
            else:
                return json.dumps((response.payload[0], escape(response.payload[1])))
        else:
            return json.dumps((False, escape('Action not defined')))

    def GET(self, action=None, name=None):

        if action == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_GET_ALL, payload=action,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)

        elif action == 'config':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload[0]:

                groupName = response.payload[1]['templateDevGrp']
                storageName = response.payload[1]['templateConfigSource']
                storage = self.storageFact.init_plugin(plugin_name=storageName)
                status, msg = storage.get_config_template_data(serialnumber=name, templateName=name,
                                                               groupName=groupName, isRaw=True)

                if status:
                    return json.dumps((status, msg))
                else:
                    return json.dumps((status, escape(msg)))
            else:
                return json.dumps((response.payload[0], escape(response.payload[1])))
        else:
            return json.dumps((False, escape('Action not defined')))


class Group(RestBase):
    exposed = True

    @cherrypy.tools.yaml_tool()
    def POST(self, action=None, name=None, descr=None, storage=None):

        if action == 'add':

            if name and storage:

                new_group = cherrypy.serving.request.unserialized_data

                payload = {'groupName': name, 'groupConfig': new_group, 'groupDescr': descr,
                           'groupConfigSource': storage}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.add_group_data(groupName=name, groupData=new_group)

                    if status:
                        return json.dumps((response.payload[0], escape(response.payload[1])))

                    else:
                        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_DEL, payload=name,
                                              source=c.AMQP_PROCESSOR_REST)
                        response = self._backendp.call(message=message)
                        response = jsonpickle.decode(response)

                        if response.payload[0]:
                            return json.dumps((status, escape(msg)))

                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

            else:
                return json.dumps((False, escape('Mandatory value missing')))

        elif action == 'del':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload[0]:

                storage = response.payload[1]['groupConfigSource']

                if response.payload[0]:

                    message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_DEL, payload=name,
                                          source=c.AMQP_PROCESSOR_REST)
                    response = self._backendp.call(message=message)
                    response = jsonpickle.decode(response)

                    if response.payload[0]:

                        storage = self.storageFact.init_plugin(plugin_name=storage)
                        status, msg = storage.del_group_data(groupName=name)

                        if status:
                            return json.dumps((response.payload[0], escape(response.payload[1])))

                        else:
                            return json.dumps((status, escape(msg)))
                    else:
                        return json.dumps((response.payload[0], escape(response.payload[1])))
                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))
            else:
                return json.dumps((response.payload[0], escape(response.payload[1])))
        else:
            return json.dumps((False, escape('Action not defined')))

    def GET(self, action=None, name=None):

        if action == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_ALL, payload=action,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps((response.payload[0], response.payload[1]))

        elif action == 'config':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload[0]:

                storageName = response.payload[1]['groupConfigSource']
                storage = self.storageFact.init_plugin(plugin_name=storageName)
                status, msg = storage.get_group_data(serialnumber=name, groupName=name, isRaw=True)

                return json.dumps((status, msg))

            else:
                return json.dumps((response.payload[0], escape(response.payload[1])))
        else:
            return json.dumps((False, escape('Action not defined')))


class Image(RestBase):
    exposed = True

    def POST(self, action=None, name=None, descr=None):

        if action == 'add':
            pass

        elif action == 'del':

            payload = {'imageName': name}
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_IMAGE_DEL, payload=payload,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            if response.payload[0]:
                # Hardcoded image dir since we do not know group at this stage
                if os.path.exists(os.getcwd() + '/images/' + name + '.tgz'):
                    os.remove('images/' + name + '.tgz')
                    return json.dumps((response.payload[0], escape(response.payload[1])))
                else:
                    return json.dumps(response.payload[0], 'File \<{0}\> not found'.format(name))
            else:
                return json.dumps((response.payload[0], escape(response.payload[1])))
        else:
            return json.dumps((False, escape('Action not defined')))

    def GET(self, action=None, name=None):

        if action == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_IMAGE_GET_ALL, payload=action,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)

        else:

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_IMAGE_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)


class Site(RestBase):
    exposed = True

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, action=None, name=None):

        if action == 'add':

            input_json = cherrypy.request.json
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_ADD, payload=input_json,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps((response.payload[0], escape(response.payload[1])))

        elif action == 'del':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_DEL, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps((response.payload[0], escape(response.payload[1])))

        else:
            return json.dumps((False, escape('Action not defined')))

    def GET(self, siteId=None):

        if siteId == 'all':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_GET_ALL, payload=siteId,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps((response.payload[0], response.payload[1]))

        else:

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SITE_GET_BY_ID, payload=siteId,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps((response.payload[0], response.payload[1]))


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

            return json.dumps((response.payload[0], escape(response.payload[1])))

        elif action == 'map':

            input_json = cherrypy.request.json
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_UPDATE, payload=input_json,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps((response.payload[0], escape(response.payload[1])))

        else:
            return json.dumps((False, escape('Action not defined')))

    @cherrypy.tools.json_out()
    def GET(self, action=None, serial=None):

        if action == 'getBySiteId':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_GET_BY_SITE, payload=serial,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            # return json.dumps((response.payload[0], response.payload[1]))
            return response.payload[0], response.payload[1]

        elif action == 'getByAssetSerial':

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_ASSET_GET_BY_SERIAL, payload=serial,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            # return json.dumps((response.payload[0], response.payload[1]))
            return response.payload[0], response.payload[1]

        else:
            # return json.dumps((False, escape('Action not defined')))
            return False, escape('Action not defined')


class Service(RestBase):
    exposed = True

    def GET(self, action=None, name=None):

        if action == 'all':
            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SERVICE_GET_ALL, payload=action,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)

        elif action == 'config':

            try:

                with open(os.getcwd() + '/conf/yapt/yapt.yml', 'r') as stream:

                    code = ruamel.yaml.load(stream, ruamel.yaml.RoundTripLoader)
                    code = code['SERVICES'][name]
                    output = StringIO.StringIO()
                    ruamel.yaml.dump(code, output, Dumper=ruamel.yaml.RoundTripDumper)
                    return output.getvalue()

            except EnvironmentError as ee:  # parent of IOError, OSError *and* WindowsError where available
                return json.dumps(False, ee.message)

        elif action == 'mod':

            try:

                with open(os.getcwd() + '/conf/yapt/yapt.yml', 'r') as stream:

                    y = ruamel.yaml.load(stream, ruamel.yaml.RoundTripLoader)
                    y = y['SERVICES'][name]
                    return json.dumps(y)

            except EnvironmentError as ee:  # parent of IOError, OSError *and* WindowsError where available
                return json.dumps(False, ee.message)

        else:

            message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_SERVICE_GET_BY_NAME, payload=name,
                                  source=c.AMQP_PROCESSOR_REST)
            response = self._backendp.call(message=message)
            response = jsonpickle.decode(response)

            return json.dumps(response.payload)


class Configsrc(RestBase):
    exposed = True

    def GET(self, action=None):

        if action == 'sources':
            return json.dumps((True, c.conf.SOURCE.DeviceConfSrcPlugins))
        else:
            pass


class Upload(RestBase):
    exposed = True

    def POST(self, name=None, descr=None, type=None, obj=None, objSize=None, group=None, storage=None):

        if type == 'group':

            if name and obj and objSize and storage:

                payload = {'groupName': name, 'groupConfig': None, 'groupDescr': descr,
                           'groupConfigSource': storage}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    size = 0
                    __data = StringIO.StringIO()

                    while True:
                        __data.write(obj.file.read(8192))

                        if size <= int(objSize):
                            __data.write(obj.file.read(8192))
                            break

                        size += __data.len

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.add_group_data(groupName=name, groupData=__data.getvalue())

                    if status:
                        return json.dumps((status, escape(response.payload[1])))
                    else:

                        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_GROUP_DEL, payload=name,
                                              source=c.AMQP_PROCESSOR_REST)
                        response = self._backendp.call(message=message)
                        response = jsonpickle.decode(response)

                        if response.payload[0]:
                            return json.dumps((status, escape(msg)))

                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

            else:
                return json.dumps((False, escape('Mandatory value missing')))

        elif type == 'template':

            if name and obj and objSize and group and storage:

                payload = {'templateName': name, 'templateConfig': None, 'templateDescr': descr,
                           'templateDevGrp': group, 'templateConfigSource': storage}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    size = 0
                    __data = StringIO.StringIO()

                    while True:
                        __data.write(obj.file.read(8192))

                        if size <= int(objSize):
                            __data.write(obj.file.read(8192))
                            break

                        size += __data.len

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.add_config_template_data(templateName=name, templateData=__data.getvalue(),
                                                                   groupName=group)

                    if status:
                        return json.dumps((response.payload[0], escape(response.payload[1])))

                    else:
                        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_TEMPLATE_DEL, payload=name,
                                              source=c.AMQP_PROCESSOR_REST)
                        response = self._backendp.call(message=message)
                        response = jsonpickle.decode(response)

                        if response.payload[0]:
                            return json.dumps((status, escape(msg)))
                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

            else:
                return json.dumps((False, escape('Mandatory value missing')))

        elif type == 'device':

            if name and obj and objSize and storage:

                payload = {'configSerial': name, 'configDescr': descr,
                           'configConfigSource': storage}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_CFG_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    size = 0
                    __data = StringIO.StringIO()

                    while True:
                        __data.write(obj.file.read(8192))

                        if size <= int(objSize):
                            __data.write(obj.file.read(8192))
                            break

                        size += __data.len

                    storage = self.storageFact.init_plugin(plugin_name=storage)
                    status, msg = storage.add_device_config_data(configSerial=name, configData=__data.getvalue())

                    if status:
                        return json.dumps((response.payload[0], escape(response.payload[1])))

                    else:
                        message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_DEVICE_CFG_DEL, payload=name,
                                              source=c.AMQP_PROCESSOR_REST)
                        response = self._backendp.call(message=message)
                        response = jsonpickle.decode(response)

                        if response.payload[0]:
                            return json.dumps((status, escape(msg)))

                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

            else:
                return json.dumps((False, escape('Mandatory value missing')))

        elif type == 'image':

            if name:

                payload = {'imageName': name, 'imageDescr': descr}
                message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_REST_IMAGE_ADD, payload=payload,
                                      source=c.AMQP_PROCESSOR_REST)
                response = self._backendp.call(message=message)
                response = jsonpickle.decode(response)

                if response.payload[0]:

                    size = 0
                    # images dir hardcoded sine we do not know group at this stage
                    with open('images/' + name + '.tgz', 'w') as image_file:
                        while True:
                            data = obj.file.read(8192)
                            image_file.write(data)
                            if not data:
                                break
                            size += len(data)

                    return json.dumps((response.payload[0], escape(response.payload[1])))

                else:
                    return json.dumps((response.payload[0], escape(response.payload[1])))

            else:
                return json.dumps((False, escape('Image name missing')))

        else:
            return json.dumps((False, escape('Unknown upload type')))


class Authenticate(RestBase):
    exposed = True

    def POST(self, sn=None):
        with auth_file_lock:
            with open(c.conf.SERVICES.Phs.DeviceAuthFile, 'a') as auth_file:
                auth_file.write(sn + '\n')
                return json.dumps((True, escape('Successfully added device <{0}> to trust store').format(sn)))


class Logs(RestBase):
    exposed = True

    def GET(self):



        url = 'ws://{0}:{1}/yapt/ws?clientname={2}'.format(c.conf.YAPT.WebUiAddress,
                                                           str(c.conf.YAPT.WebUiPort), c.conf.YAPT.WebUiPlugin)
        wsc = WebSocketClient(url=url)
        wsc.connect()

        #with open('./logs/info.log', 'r') as stream:
        #    log_data = stream.read()

        #if log_data:
        #    wsc.send(payload=json.dumps({'action': c.UI_ACTION_INIT_LOG_VIEWER, 'data': log_data}))

        # bufsize = 8192
        fname = './logs/info.log'
        fsize = os.stat(fname).st_size
        iter = 0
        lines = 17

        with open(fname, 'r') as f:

            bufsize = fsize - 1
            data = []

            while True:

                iter += 1
                f.seek(fsize - bufsize * iter)
                data.extend(f.readlines())

                if len(data) >= lines or f.tell() == 0:
                    #print(''.join(data[-lines:]))
                    wsc.send(payload=json.dumps({'action': c.UI_ACTION_INIT_LOG_VIEWER, 'data': ''.join(data[-lines:])}))
                    break
        wsc.close()
        pass


class YaptRestApi(object):
    """
    YAPT REST API mapping
    """

    url_map = {'device': Device, 'template': Template, 'group': Group, 'image': Image, 'service': Service,
               'configsrc': Configsrc, 'upload': Upload, 'authenticate': Authenticate, 'site': Site, 'asset': Asset,
               'logs': Logs}

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
