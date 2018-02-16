# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import importlib

import yaml

import constants as c
from lib.logmsg import LogPlgFactory as logmsg
from lib.tools import Tools


class SourcePluginFactory(object):
    def __init__(self, plugin_names):

        self.logger = c.logger
        try:

            with open("conf/plugins/mapping.yml", 'r') as mapping:
                self.plugin_cfg = yaml.load(mapping)
                self._plugin_cfg = None

                for plugin_name in plugin_names:
                    self._plugin_cfg = self.plugin_cfg[plugin_name.upper()]
                    self.logger.debug(
                        Tools.create_log_msg(logmsg.SRCPLG, None, logmsg.SRCPLG_LOAD_CFG.format(self._plugin_cfg)))
                    self.init_plugin(self._plugin_cfg)

        except IOError as err:
            self.logger.debug(Tools.create_log_msg(logmsg.SRCPLG, None,
                                                   logmsg.SRCPLG_FILE_ERROR.format(err.errno, err.strerror,
                                                                                   err.filename)))

    def init_plugin(self, plugin_cfg):
        self.logger.debug(
            Tools.create_log_msg(logmsg.SRCPLG, None, logmsg.SRCPLG_SEARCH.format(plugin_cfg['pluginName'])))
        source_plugins = Tools.load_source_plugins()

        if plugin_cfg['pluginName'] in source_plugins:
            self.logger.info(
                Tools.create_log_msg(logmsg.SRCPLG, None, logmsg.SRCPLG_FOUND.format(plugin_cfg['pluginName'])))
            # Load source plugin
            source_plugin = source_plugins[plugin_cfg['pluginName']]
            self.logger.debug(Tools.create_log_msg(logmsg.SRCPLG, None, logmsg.SRCPLG_LOAD_PLG.format(source_plugin)))
            source_plugin = getattr(source_plugin.pop(), plugin_cfg['pluginName'].title())
            self.logger.debug(Tools.create_log_msg(logmsg.SRCPLG, None, logmsg.SRCPLG_LOAD_PLG.format(source_plugin)))
            source_plugin = source_plugin(plugin_cfg=plugin_cfg)
            self.logger.debug(Tools.create_log_msg(logmsg.SRCPLG, None, logmsg.SRCPLG_LOAD_PLG.format(source_plugin)))

            # Load according to source plugin cfg proper service
            self.logger.debug(
                Tools.create_log_msg(logmsg.SVCPLG, None, logmsg.SVCPLG_SEARCH.format(plugin_cfg['serviceName'])))
            importlib.import_module('lib.services')
            service = importlib.import_module('.' + plugin_cfg['serviceName'].lower(), package="lib.services")
            self.logger.debug(Tools.create_log_msg(logmsg.SVCPLG, None, logmsg.SVCPLG_LOAD.format(service)))
            service = getattr(service, plugin_cfg['serviceName'].title())
            self.logger.debug(Tools.create_log_msg(logmsg.SVCPLG, None, logmsg.SVCPLG_LOAD.format(service)))
            service = service(source_plugin, plugin_cfg)
            self.logger.debug(Tools.create_log_msg(logmsg.SVCPLG, None, logmsg.SVCPLG_LOAD.format(service)))
            service.run_service()

        else:
            self.logger.info(
                Tools.create_log_msg(logmsg.SVCPLG, None, logmsg.SVCPLG_NOT_FOUND.format(plugin_cfg['serviceName'])))


class BackendPluginFactory(object):
    def __init__(self, plugin_name=None, target=None, name='backend'):

        self.logger = c.logger
        self._plugin_name = plugin_name
        self._target = target
        self._name = name
        self.init_plugin()

    def init_plugin(self):

        self.logger.info(
            Tools.create_log_msg(logmsg.BACKENDPLG, None, logmsg.BACKENDPLG_SEARCH.format(self._plugin_name)))

        backend_plugins = Tools.load_backend_plugins()

        if self._plugin_name in backend_plugins:
            self.logger.debug(
                Tools.create_log_msg(logmsg.BACKENDPLG, None, logmsg.BACKENDPLG_FOUND.format(self._plugin_name)))
            backend_plugin = backend_plugins[self._plugin_name]
            self.logger.debug(Tools.create_log_msg(logmsg.BACKENDPLG, None,
                                                   logmsg.BACKENDPLG_LOAD.format(backend_plugin)))
            backend_plugin = getattr(backend_plugin.pop(), self._plugin_name.title())
            self.logger.debug(Tools.create_log_msg(logmsg.BACKENDPLG, None,
                                                   logmsg.BACKENDPLG_LOAD.format(backend_plugin)))
            backend_plugin = backend_plugin(target=self._target, name=self._name,
                                            args=(c.conf.AMQP.Exchange, c.conf.AMQP.Type,
                                                  c.AMQP_RPC_BACKEND_QUEUE,))
            self.logger.debug(Tools.create_log_msg(logmsg.BACKENDPLG, None,
                                                   logmsg.BACKENDPLG_LOAD.format(backend_plugin)))
            backend_plugin.start()

        else:
            self.logger.info(Tools.create_log_msg(logmsg.BACKENDPLG, None,
                                                  logmsg.BACKENDPLG_NOT_FOUND.format(self._plugin_name)))


class SpacePluginFactory(object):
    def __init__(self, plugin_name=None):
        self.logger = c.logger
        self._plugin_name = plugin_name

    def init_plugin(self):
        self.logger.info(Tools.create_log_msg(logmsg.SPACEPLG, None,
                                              logmsg.SPACEPLG_SEARCH.format(self._plugin_name)))
        space_plugins = Tools.load_space_plugins()

        if self._plugin_name in space_plugins:
            self.logger.debug(Tools.create_log_msg(logmsg.SPACEPLG, None,
                                                   logmsg.SPACEPLG_FOUND.format(self._plugin_name)))
            space_plugin = space_plugins[self._plugin_name]
            self.logger.debug(Tools.create_log_msg(logmsg.SPACEPLG, None,
                                                   logmsg.SPACEPLG_LOAD.format(space_plugin)))
            space_plugin = getattr(space_plugin.pop(), self._plugin_name.title())
            self.logger.debug(Tools.create_log_msg(logmsg.SPACEPLG, None,
                                                   logmsg.SPACEPLG_LOAD.format(space_plugin)))
            space_plugin = space_plugin(space_ip=c.conf.JUNOSSPACE.Ip, space_user=c.conf.JUNOSSPACE.User,
                                        space_password=Tools.get_password(c.YAPT_PASSWORD_TYPE_SPACE))
            self.logger.debug(Tools.create_log_msg(logmsg.SPACEPLG, None,
                                                   logmsg.SPACEPLG_LOAD.format(space_plugin)))
            return space_plugin

        else:
            self.logger.debug(Tools.create_log_msg(logmsg.SPACEPLG, None,
                                                   logmsg.SPACEPLG_NOT_FOUND.format(self._plugin_name)))
            return None


class EmitterPlgFact(object):

    def __init__(self):
        self.init_plugin()

    def init_plugin(self):

        if c.conf.EMITTER.Plugins:

            emitter_plgs = Tools.load_emitter_plugins()

            print Tools.create_log_msg(self.__class__.__name__, None,
                                       'Loading emitter plugin sequence <{0}>'.format(c.conf.EMITTER.Plugins))

            for _plg_name, _log_plg in emitter_plgs.iteritems():

                emitter_plugin = emitter_plgs[_plg_name]
                emitter_plugin = getattr(emitter_plugin.pop(), _plg_name.title())
                emitter_plugin = emitter_plugin()
                c.active_log_plgs[_plg_name.title()] = emitter_plugin
        else:
            print Tools.create_log_msg(self.__class__.__name__, None, 'Emitter plugin sequence is empty')
