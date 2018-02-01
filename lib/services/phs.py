# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import datetime
import multiprocessing
import os

import cherrypy
from cherrypy._cpserver import Server
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from lxml import etree

from lib.amqp.amqpmessage import AMQPMessage
import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import Logphs as logmsg
from lib.services.service import Service
from lib.tools import Tools


class Phs(Service):
    def __init__(self, source_plugin, plugin_cfg):

        super(Phs, self).__init__(source_plugin=source_plugin, plugin_cfg=plugin_cfg)
        self._devices_auth = dict()
        self.logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Phs, Service))))
        self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None, logmsg.PHS_START))

    def validate_phc(self, realm, username, password):

        if os.path.isfile(c.conf.SERVICES.Phs.DeviceAuthFile):

            for line in open(c.conf.SERVICES.Phs.DeviceAuthFile):

                if line not in self._devices_auth:
                    self._devices_auth[line.rstrip('\n')] = ''

            if len(username) == 12:

                if username in self._devices_auth and self._devices_auth[username] == password:
                    self.logger.info(
                        Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                             logmsg.PHS_VALIDATION_SUCCESS.format(username)))
                    return True

                else:
                    self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                                          logmsg.PHS_VALIDATION_FAILED.format(username)))
                    return False

            else:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                                      logmsg.PHS_VALIDATION_FAILED.format(username)))
                return False

        else:
            self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                                  logmsg.PHS_VALIDATION_FAILED.format(username)))
            return False

    def run_service(self):

        if c.conf.SERVICES.Phs.Containerized:

            p = multiprocessing.Process(target=PhsInitC, args=(self.source_plugin, self.plugin_cfg))
            p.start()

        else:

            phs = PhoneHomeServer(self.source_plugin, self.plugin_cfg)
            rd = cherrypy.dispatch.RoutesDispatcher()
            rd.connect('phs', c.PHS_INIT_URL, controller=phs, action='init')
            # rd.connect('phs', '/restconf/data/juniper-zerotouch-bootstrap-server:devices/device={uid}/activation-code',
            #           controller=phs, action='activation')
            rd.connect('phs', c.PHS_NOTIFICATION_URL, controller=phs, action='notification')

            conf = {
                '/': {
                    'log.screen': False,
                    'request.dispatch': rd,
                    'tools.auth_basic.on': True,
                    'tools.auth_basic.realm': 'localhost',
                    'tools.auth_basic.checkpassword': self.validate_phc
                }
            }
            cherrypy.tree.mount(root=None, config=conf)


class PhsInitC(object):

    def __init__(self, source_plugin, plugin_cfg):
        self._devices_auth = dict()
        self.logger = c.logger

        phs = PhoneHomeServer(source_plugin, plugin_cfg)
        rd = cherrypy.dispatch.RoutesDispatcher()
        rd.connect('phs', c.PHS_INIT_URL, controller=phs, action='init')
        # rd.connect('phs', '/restconf/data/juniper-zerotouch-bootstrap-server:devices/device={uid}/activation-code',
        #           controller=phs, action='activation')
        rd.connect('phs', c.PHS_NOTIFICATION_URL, controller=phs, action='notification')
        cherrypy.config.update({'engine.autoreload.on': False})
        conf = {
            '/': {
                'log.screen': False,
                'request.dispatch': rd,
                'tools.auth_basic.on': True,
                'tools.auth_basic.realm': 'localhost',
                'tools.auth_basic.checkpassword': self.validate_phc
            }
        }
        cherrypy.tree.mount(root=None, config=conf)
        cherrypy.engine.start()
        cherrypy.engine.block()

    def validate_phc(self, realm, username, password):

        if os.path.isfile(c.conf.SERVICES.Phs.DeviceAuthFile):

            for line in open(c.conf.SERVICES.Phs.DeviceAuthFile):

                if line not in self._devices_auth:
                    self._devices_auth[line.rstrip('\n')] = ''

            if len(username) == 12:

                if username in self._devices_auth and self._devices_auth[username] == password:
                    self.logger.info(
                        Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                             logmsg.PHS_VALIDATION_SUCCESS.format(username)))
                    return True

                else:
                    self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                                          logmsg.PHS_VALIDATION_FAILED.format(username)))
                    return False

            else:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                                      logmsg.PHS_VALIDATION_FAILED.format(username)))
                return False

        else:
            self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                                  logmsg.PHS_VALIDATION_FAILED.format(username)))
            return False


class PhoneHomeServer(object):
    def __init__(self, source_plugin, plugin_cfg):
        self.logger = c.logger
        self._phs_server = Server()
        self._phs_server.socket_host = c.conf.SERVICES.Phs.ServiceBindAddress
        self._phs_server.socket_port = c.conf.SERVICES.Phs.ServiceListenPort
        self.device_type = None
        self.service_chain = None
        self.deviceIP = None
        self.serialnumber = None

        if c.conf.SERVICES.Phs.EnableSSL:

            self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None, logmsg.PHS_SSL_ENABLED))
            self._phs_server.ssl_module = 'builtin'

            if os.path.isfile(c.conf.SERVICES.Phs.SSLCertificate):
                self._phs_server.ssl_certificate = c.conf.SERVICES.Phs.SSLCertificate

            else:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None, logmsg.PHS_SSL_NO_CERT))

            if os.path.isfile(c.conf.SERVICES.Phs.SSLPrivateKey):
                self._phs_server.ssl_private_key = c.conf.SERVICES.Phs.SSLPrivateKey
            else:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None, logmsg.PHS_SSL_NO_KEY))

        self._phs_server.subscribe()
        self._source_plugin = source_plugin
        self._plugin_cfg = plugin_cfg
        self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None, logmsg.PHS_LISTEN))

    @cherrypy.expose
    def init(self, **params):

        self.deviceIP = cherrypy.request.headers['Remote-Addr']
        self.serialnumber = params['uid']
        from lib.tasks.tasktools import Configuration
        _configurator = Configuration()
        datavars = _configurator.get_device_config(
            serialnumber=self.serialnumber, deviceOsshId=None, lookup_type=c.CONFIG_SOURCE_LOOKUP_TYPE_DEVICE)

        if datavars:

            try:

                self.device_type = datavars['yapt']['device_type']
                self.service_chain = datavars['yapt']['service_chain']

            except KeyError as ke:
                self.logger.info(
                    '{0} {1}'.format(logmsg.PHS_SERVICE + ':', logmsg.PHS_CONF_KEY_ERROR.format(ke.message)))
                return

            _boostrap_init_file = c.conf.SERVICES.Phs.InitConfPath + self.device_type + '.xml'

            if os.path.isfile(_boostrap_init_file):
                response = None

                try:
                    env = Environment(autoescape=select_autoescape(['xml']),
                                      loader=FileSystemLoader(c.conf.SERVICES.Phs.InitConfPath),
                                      trim_blocks=True, lstrip_blocks=True)
                    response = env.get_template(self.device_type + '.xml').render(serial=self.serialnumber)

                except (TemplateNotFound, IOError) as err:
                    self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                          logmsg.PHS_TEMPLATE_ERROR.format(err.errno,
                                                                                           err.strerror,
                                                                                           err.filename)))
                return response

            else:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                      logmsg.PHS_BOOSTRAP_FILE_FAILED.format(_boostrap_init_file)))

        else:
            self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber, logmsg.PHS_DEV_CONF_FAILED))

    @cherrypy.expose
    def activation(self, **params):
        pass

    @cherrypy.expose
    def notification(self, **params):

        cherrypy.response.status = 201
        body = cherrypy.request.body.read()
        xml_body = etree.fromstring(body)
        ns_orig = 'http://juniper.net/zerotouch-bootstrap-server'

        for item in xml_body.iter('{' + ns_orig + '}notification-type'):

            if item.text == c.PHS_NOTIFICATION_CONF_APPLIED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                      logmsg.PHS_STAGE1_SUCCESS).format(params['uid']))

            elif item.text == c.PHS_NOTIFICATION_CONF_FAILED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                      logmsg.PHS_STAGE1_FAILED.format(params['uid'])))

            elif item.text == c.PHS_NOTIFICATION_BOOTSTRAP_COMPLETED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                      logmsg.PHS_BOOTSTRAP_SUCCESS.format(params['uid'])))

                if c.SOURCEPLUGIN_OSSH in self.service_chain:
                    self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                          logmsg.PHS_SEC_SVC.format(c.SOURCEPLUGIN_OSSH,
                                                                                    c.SOURCEPLUGIN_OSSH)))
                    return

                else:
                    sample_device = self._source_plugin.run_source_plugin(
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), device=self.deviceIP)

                    # NFX JDM facts return empty serial number so we have to add it here
                    # if self.device_type == 'nfx':
                    sample_device.deviceSerial = self.serialnumber

                    message = AMQPMessage(message_type=c.AMQP_MESSAGE_TYPE_DEVICE_ADD,
                                          payload=sample_device,
                                          source=c.AMQP_PROCESSOR_SVC)
                    self._source_plugin.send_message(message=message)

            elif item.text == c.PHS_NOTIFICATION_BOOTSTRAP_FAILED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.serialnumber,
                                                      logmsg.PHS_BOOSTRAP_FAILED.format(params['uid'])))
