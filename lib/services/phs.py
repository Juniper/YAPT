# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import datetime
import multiprocessing
import os

import jsonpickle
import cherrypy
import lib.constants as c

from cherrypy._cpserver import Server
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from lxml import etree

from lib.amqp.amqpmessage import AMQPMessage
from lib.processor import BackendClientProcessor

from lib.logmsg import LogCommon
from lib.logmsg import Logphs as logmsg
from lib.services.service import Service
from lib.tools import Tools


class Phs(Service):

    def __init__(self, normalizer, svc_cfg):

        super(Phs, self).__init__(normalizer=normalizer, svc_cfg=svc_cfg)
        self._stop_service = multiprocessing.Event()
        self.p = None
        self.logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                               LogCommon.IS_SUBCLASS.format(self.__class__.__name__,
                                                                            issubclass(Phs, Service))))
        self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None, logmsg.PHS_START))

    def start_service(self):

        if self.status == c.SVC_STOPPED or self.status == c.SVC_INIT:
            self.p = multiprocessing.Process(target=PhsInitC, args=(self.normalizer, self.svc_cfg))
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
                Tools.create_log_msg(logmsg.PHS_SERVICE, None,
                                     logmsg.PHS_STOPPED.format(c.conf.SERVICES.Phs.ServiceBindAddress,
                                                               c.conf.SERVICES.Phs.ServiceListenPort)))
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


@cherrypy.tools.register('before_finalize', priority=60)
def secureHeaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['X-Content-Type-Options'] = 'nosniff'
    headers['Content-Security-Policy'] = "default-src='self'"

    if cherrypy.server.ssl_certificate is not None and cherrypy.server.ssl_private_key is not None:
        headers['Strict-Transport-Security'] = 'max-age=31536000'


class PhsInitC(object):

    def __init__(self, source_plugin, plugin_cfg):
        self._devices_auth = dict()
        self.logger = c.logger
        self._backendp = BackendClientProcessor(exchange='', routing_key=c.AMQP_RPC_BACKEND_QUEUE)
        cherrypy.config.update('{0}/{1}'.format(os.getcwd(), c.SVC_PHS_CONF))
        phs = PhoneHomeServer(source_plugin, plugin_cfg)
        rd = cherrypy.dispatch.RoutesDispatcher()
        rd.connect('phs', c.PHS_INIT_URL, controller=phs, action='init')
        # rd.connect('phs', '/restconf/data/juniper-zerotouch-bootstrap-server:devices/device={uid}/activation-code',
        #           controller=phs, action='activation')
        rd.connect('phs', c.PHS_NOTIFICATION_URL, controller=phs, action='notification')

        conf = {
            '/': {
                'request.dispatch': rd,
                'tools.auth_basic.checkpassword': self.validate_phc
            }
        }

        app = cherrypy.tree.mount(root=None, config='{0}/{1}'.format(os.getcwd(), c.SVC_PHS_CONF))
        app.merge(conf)
        cherrypy.engine.start()
        cherrypy.engine.block()

    def validate_phc(self, realm, username, password):

        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_SVC_PHS_VALIDATE,
                              payload={'username': username, 'password': password},
                              source=c.AMQP_PROCESSOR_TASK)

        resp = self._backendp.call(message=message)
        resp = jsonpickle.decode(resp)

        if resp.payload[0]:
            self.logger.info(
                Tools.create_log_msg(logmsg.PHS_SERVICE, username,
                                     logmsg.PHS_VALIDATION_SUCCESS.format(username)))
            return True
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
        self.sn_nr = None

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
        self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, None,
                                              logmsg.PHS_LISTEN.format(self._phs_server.socket_host,
                                                                       self._phs_server.socket_port)))

    @cherrypy.expose
    def init(self, **params):

        self.deviceIP = cherrypy.request.headers['Remote-Addr']
        self.sn_nr = params['uid']
        status, data = Tools.get_config(lookup_type=c.CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG,
                                        serialnumber=self.sn_nr, deviceOsshId=None)

        if status:

            try:

                self.device_type = data['yapt']['device_type']
                self.service_chain = data['yapt']['service_chain']

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
                    response = env.get_template(self.device_type + '.xml').render(serial=self.sn_nr)

                except (TemplateNotFound, IOError) as err:
                    self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                          logmsg.PHS_TEMPLATE_ERROR.format(err.errno,
                                                                                           err.strerror,
                                                                                           err.filename)))
                return response

            else:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                      logmsg.PHS_BOOSTRAP_FILE_FAILED.format(_boostrap_init_file)))

        else:
            self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr, logmsg.PHS_DEV_CONF_FAILED))

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
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                      logmsg.PHS_STAGE1_SUCCESS).format(params['uid']))

            elif item.text == c.PHS_NOTIFICATION_CONF_FAILED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                      logmsg.PHS_STAGE1_FAILED.format(params['uid'])))

            elif item.text == c.PHS_NOTIFICATION_BOOTSTRAP_COMPLETED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                      logmsg.PHS_BOOTSTRAP_SUCCESS.format(params['uid'])))

                if c.SOURCEPLUGIN_OSSH in self.service_chain:
                    self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                          logmsg.PHS_SEC_SVC.format(c.SOURCEPLUGIN_OSSH,
                                                                                    c.SOURCEPLUGIN_OSSH)))
                    return

                else:
                    sample_device = self._source_plugin.run_normalizer(
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), device=self.deviceIP)

                    # NFX JDM facts return empty serial number so we have to add it here
                    if self.device_type == 'nfx':
                        sample_device.deviceSerial = self.sn_nr

                    message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD,
                                          payload=sample_device,
                                          source=c.AMQP_PROCESSOR_SVC)
                    self._source_plugin.send_message(message=message)

            elif item.text == c.PHS_NOTIFICATION_BOOTSTRAP_FAILED:
                self.logger.info(Tools.create_log_msg(logmsg.PHS_SERVICE, self.sn_nr,
                                                      logmsg.PHS_BOOSTRAP_FAILED.format(params['uid'])))
