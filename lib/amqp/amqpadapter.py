# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import abc
import sys
import threading

import pika
from pika import exceptions

from lib.logmsg import LogAmqp as logmsg
import lib.constants as c
from lib.tools import Tools


class AMQPBlockingServerAdapter(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):

        """

        :param group:
        :param target:
        :type target: Processor
        :param name:
        :param args:
        :param kwargs:
        """

        super(AMQPBlockingServerAdapter, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)

        self._exchange = args[0]
        self._type = args[1]
        self._routing_key = args[2]
        self._queue = args[3]
        self._logger = c.logger

        try:

            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=c.conf.AMQP.Host, port=c.conf.AMQP.Port,
                                          credentials=pika.PlainCredentials(c.conf.AMQP.User,
                                                                            Tools.get_password(
                                                                                c.YAPT_PASSWORD_TYPE_AMQP))))
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self._queue, durable=False)
            self._channel.basic_qos(prefetch_count=1)
            self._channel.basic_consume(self.receive_message, queue=self._routing_key)

        except exceptions.ConnectionClosed as err:
            print Tools.create_log_msg('AMQP', None, logmsg.AMQP_BUS_NOK.format(err))
            self._logger.info(Tools.create_log_msg('AMQP', None, logmsg.AMQP_BUS_NOK.format(err)))
            sys.exit()

        Tools.create_amqp_startup_log(exchange=self._exchange, type=self._type,
                                      routing_key=self._routing_key,
                                      host=c.conf.AMQP.Host,
                                      channel=self._channel)

    def run(self):
        self._channel.start_consuming()

    def send_message_amqp(self, message, routing_key):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=c.conf.AMQP.Host, port=c.conf.AMQP.Port,
                                      credentials=pika.PlainCredentials(c.conf.AMQP.User,
                                                                        Tools.get_password(
                                                                            c.YAPT_PASSWORD_TYPE_AMQP))))
        channel = connection.channel()
        channel.queue_declare(queue=self._routing_key, durable=False)

        channel.basic_publish(exchange='',
                              routing_key=routing_key,
                              body=message,
                              properties=pika.BasicProperties(
                                  delivery_mode=1,
                              ))
        connection.close()

    @abc.abstractmethod
    def receive_message(self, ch, method, properties, body):
        raise NotImplementedError()


class AMQPRpcServerAdapter(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        """

        :param group:
        :param target:
        :type target: type: Processor
        :param name:
        :param args:
        :param kwargs:
        """

        super(AMQPRpcServerAdapter, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._exchange = args[0]
        self._type = args[1]
        self._routing_key = args[2]
        self._logger = c.logger

        try:

            self._connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=c.conf.AMQP.Host, port=c.conf.AMQP.Port,
                credentials=pika.PlainCredentials(c.conf.AMQP.User,
                                                  Tools.get_password(
                                                      c.YAPT_PASSWORD_TYPE_AMQP))))
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self._routing_key)
            self._channel.basic_qos(prefetch_count=1)
            self._channel.basic_consume(self.on_request, queue=self._routing_key)

        except (exceptions.ProbableAuthenticationError, exceptions.ConnectionClosed) as err:
            print Tools.create_log_msg('AMQP', None, logmsg.AMQP_BUS_NOK.format(err))
            self._logger.info(Tools.create_log_msg('AMQP', None, logmsg.AMQP_BUS_NOK.format(err)))
            sys.exit()

        Tools.create_amqp_startup_log(exchange=self._exchange, type=self._type,
                                      routing_key=self._routing_key,
                                      host=c.conf.AMQP.Host, channel=self._channel)

    def run(self):
        self._channel.start_consuming()

    @abc.abstractmethod
    def on_request(self, ch, method, props, body):
        raise NotImplementedError()


class AMQPBlockingClientAdapter(object):
    def __init__(self, exchange=None, routing_key=None, queue=None):
        self._exchange = exchange
        self._routing_key = routing_key
        self._queue = queue
        self._logger = c.logger

    def send_message_amqp(self, message):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=c.conf.AMQP.Host, port=c.conf.AMQP.Port,
                                      credentials=pika.PlainCredentials(c.conf.AMQP.User,
                                                                        Tools.get_password(
                                                                            c.YAPT_PASSWORD_TYPE_AMQP))))
        channel = connection.channel()
        channel.queue_declare(queue=self._queue, durable=False)

        channel.basic_publish(exchange='',
                              routing_key=self._routing_key,
                              body=message,
                              properties=pika.BasicProperties(
                                  delivery_mode=1,
                              ))
        connection.close()


class AMQPRpcClientAdapter(object):
    def __init__(self, exchange=None, routing_key=None):

        self._exchange = exchange
        self._routing_key = routing_key
        self._logger = c.logger

        try:

            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=c.conf.AMQP.Host, port=c.conf.AMQP.Port,
                                          credentials=pika.PlainCredentials(c.conf.AMQP.User,
                                                                            Tools.get_password(
                                                                                c.YAPT_PASSWORD_TYPE_AMQP))))
            self._channel = self._connection.channel()
            self._result = self._channel.queue_declare(exclusive=True)
            self._callback_queue = self._result.method.queue
            self._channel.basic_consume(self.on_response, no_ack=True, queue=self._callback_queue)
            self._response = None
            self._corr_id = None

        except pika.exceptions.ConnectionClosed as err:
            print Tools.create_log_msg('AMQP', None, logmsg.AMQP_BUS_NOK.format(err))
            self._logger.info(Tools.create_log_msg('AMQP', None, logmsg.AMQP_BUS_NOK.format(err)))

    @abc.abstractmethod
    def call(self, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def on_response(self, ch, method, props, body):
        raise NotImplementedError()
