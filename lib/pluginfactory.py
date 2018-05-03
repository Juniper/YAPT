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


class ServicePluginFactory(object):

    def __init__(self, plugin_names):
        self.logger = c.logger
        self.registry = dict()
        #normalizer = [Tools.load_service_normalizer(service=service) for service in c.conf.SERVICES.Plugins]
        importlib.import_module('lib.services')

        for service in c.conf.SERVICES.Plugins:
            svc_cfg = ServicePluginFactory.get_svc_cfg(service=service)

            for k in svc_cfg:
                normalizer = Tools.load_service_normalizer(service=k.keys()[0])
                self.init_plugin(service, k.values()[0], normalizer)

    @staticmethod
    def get_svc_cfg(service=None):
        svc = getattr(c.conf.SERVICES, service)
        n = getattr(svc, 'Normalizer')

        if isinstance(n, list):

            for item in n:

                plugin = getattr(svc, item)
                module = getattr(plugin, plugin.Module, None)
                save = dict()

                if module:
                    save[item] = {'svcName': service, 'LogFile': plugin.LogFile, 'Module': getattr(plugin, plugin.Module, None)}
                    yield save

                else:
                    save[item] = {'svcName': service, 'LogFile': plugin.LogFile, 'Module': plugin}
                    yield save

        elif isinstance(n, str):
            yield {service: svc}

    def init_plugin(self, service_name, svc_cfg, normalizer):

        service = importlib.import_module('.' + service_name.lower(), package="lib.services")
        service = getattr(service, service_name)
        service = service(normalizer(svc_cfg=svc_cfg), svc_cfg)
        self.registry[service_name] = service
        service.start_service()


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


class StoragePlgFact(object):

    def __init__(self):
        self.logger = c.logger

    def init_plugins(self):

        if c.conf.STORAGE.DeviceConfSrcPlugins:

            storage_plgs = Tools.load_storage_plugins()
            active_storage_plgs = dict()

            self.logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                   'Loading storage plugin sequence <{0}>'.format(
                                                       c.conf.STORAGE.DeviceConfSrcPlugins)))

            for _plg_name, _storage_plg in storage_plgs.iteritems():
                storage_plugin = storage_plgs[_plg_name]
                storage_plugin = getattr(storage_plugin.pop(), _plg_name.title())
                storage_plugin = storage_plugin()
                active_storage_plgs[_plg_name.title()] = storage_plugin

            self.logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                   'Successfully loaded storage plugin sequence <{0}>'.format(
                                                       c.conf.STORAGE.DeviceConfSrcPlugins)))
            return active_storage_plgs

        else:
            self.logger.info(Tools.create_log_msg(self.__class__.__name__, None, 'Storage plugin sequence is empty'))

    def init_plugin(self, plugin_name=None):

        if c.conf.STORAGE.DeviceConfSrcPlugins:

            self.logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                   'Loading storage plugin <{0}>'.format(plugin_name)))

            storage = Tools.load_storage_plugin(name=plugin_name)
            self.logger.debug(logmsg.STORAGE_PLG, plugin_name,
                              logmsg.STORAGE_PLG_FOUND.format(plugin_name))
            storage = getattr(storage, plugin_name.title())
            self.logger.debug(logmsg.STORAGE_PLG, plugin_name,
                              logmsg.STORAGE_PLG_LOADED.format(plugin_name))
            storage = storage()
            self.logger.debug(Tools.create_log_msg(self.__class__.__name__, None,
                                                   'Successfully loaded storage plugin <{0}>'.format(plugin_name)))
            return storage

        else:
            self.logger.info(Tools.create_log_msg(self.__class__.__name__, None, 'Storage plugin sequence is empty'))
