# Copyright (c) 2017, Juniper Networks Inc.
# All rights reserved.
#

import os

import cherrypy
from cherrypy._cpserver import Server
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from lib.logmsg import LogYaptOobaUi as logmsg
import lib.constants as c
from lib.tools import Tools

env = Environment(loader=FileSystemLoader('lib/web/ooba'))


class YaptOoba(object):
    """
    YAPT Out of band activation
    """

    def __init__(self):
        self._host = c.conf.YAPT.WebUiAddress
        self._port = int(c.conf.YAPT.OobaUiPort)
        self._current_dir = os.path.dirname(os.path.abspath(__file__))

        yapt_rest_server = Server()
        yapt_rest_server.socket_host = self._host
        yapt_rest_server.socket_port = self._port
        yapt_rest_server.subscribe()

    @cherrypy.expose
    def index(self):

        if c.conf.YAPT.WebUiProxy:
            _host = c.conf.YAPT.WebUiProxyIp
            _port = int(c.conf.YAPT.OobaUiProxyPort)
        else:
            _host = self._host
            _port = self._port

        try:

            tmpl = env.get_template('ooba.html')
            index = tmpl.render(host=_host, port=_port)

            return index
        except (TemplateNotFound, IOError) as ioe:

            Tools.create_log_msg(self.__class__.__name__, '',
                                 logmsg.OOBA_FILE_NOK.format(ioe.filename if ioe.filename else ioe))
            return logmsg.OOBA_FILE_NOK.format(ioe.filename if ioe.filename else ioe)
