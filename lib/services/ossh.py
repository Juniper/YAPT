# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Authors: cklewar@juniper.net
#

import datetime
import hashlib
import hmac
import socket
import sys
import threading

import paramiko
from paramiko import BadHostKeyException, AuthenticationException, SSHException
from scp import SCPClient

from lib.amqp.amqpmessage import AMQPMessage
import lib.constants as c
from lib.logmsg import LogCommon
from lib.logmsg import Logossh as logmsg
from lib.services.service import Service
from lib.tools import Tools


class Ossh(Service):
    def __init__(self, normalizer, svc_cfg):
        super(Ossh, self).__init__(normalizer=normalizer, svc_cfg=svc_cfg)
        self.logger.debug(Tools.create_log_msg(logmsg.OSSH_SERVICE, None,
                                               LogCommon.IS_SUBCLASS.format(logmsg.OSSH_SERVICE,
                                                                            issubclass(Ossh, Service))))
        self.logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, None, logmsg.OSSH_START))
        self.ossh_svc_t = None

    def start_service(self):

        if self.status == c.SVC_STOPPED or self.status == c.SVC_INIT:

            self.ossh_svc_t = OSSHServiceThread(target=None, name=self.svc_cfg['serviceName'],
                                                args=('OSSH', self.normalizer, self.status))
            self.ossh_svc_t.start()
            self.status = c.SVC_STARTED
            return self.status
        else:
            return self.status

    def stop_service(self):

        if self.status == c.SVC_STARTED:

            self.ossh_svc_t.stop()
            # self._sock.shutdown(socket.SHUT_RDWR)
            self.ossh_svc_t.join()
            self.status = c.SVC_STOPPED
            self.logger.info(
                Tools.create_log_msg(logmsg.OSSH_SERVICE, None,
                                     logmsg.OSSH_STOPPED.format(c.conf.SERVICES.Ossh.ServiceBindAddress,
                                                                c.conf.SERVICES.Ossh.ServiceListenPort)))
            return self.status

        else:
            return self.status

    def restart_service(self):

        if self.status == c.SVC_STOPPED:

            self.start_service()
            return self.status
        else:

            self.stop_service()
            self.ossh_svc_t.join()
            self.start_service()
            return self.status


class OSSHServiceThread(threading.Thread):
    """
            OSSHServer class provides socket for SSH, reverse ssh connection and port forwarding
        """

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        """
        :param target:
        :param name: OSSHServer thread name
        :param args: [0]=logmodule name, [1]=source_plugin
        :return:
        """

        super(OSSHServiceThread, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)
        self._logger = c.logger
        self._logmodule = args[0]
        self._source_plugin = args[1]
        self.status = args[2]
        self._stop_service = threading.Event()
        self._ssh_server_bind_address = c.conf.SERVICES.Ossh.ServiceBindAddress
        self._ssh_server_listen_port = c.conf.SERVICES.Ossh.ServiceListenPort
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self._sock.bind((self._ssh_server_bind_address, self._ssh_server_listen_port))

        except socket.error as se:

            self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, self._ssh_server_bind_address,
                                                   logmsg.OSSH_BIND_FAILED.format(se.strerror)))
            self._logger.info(
                Tools.create_log_msg(logmsg.OSSH_SERVICE, self._ssh_server_bind_address, logmsg.OSSH_BIND_FAILED_1))
            sys.exit(1)

    def stop(self):
        self._stop_service.set()
        self._sock.close()

    def run(self):

        try:
            self._sock.listen(5)
            self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, None,
                                                   logmsg.OSSH_LISTEN.format(self._ssh_server_bind_address,
                                                                             self._ssh_server_listen_port)))
            self.status = c.SVC_STARTED

        except Exception as e:
            self._logger.info(
                Tools.create_log_msg(logmsg.OSSH_SERVICE, None, logmsg.OSSH_LISTEN_FAILED.format(e)))
            sys.exit(1)

        while self._stop_service.is_set():

            sock, sock_addr = self._sock.accept()
            sock.settimeout(60)
            self._logger.info(
                Tools.create_log_msg(logmsg.OSSH_SERVICE, sock_addr[0], logmsg.OSSH_NEW_CONN.format(sock_addr)))
            isTrusted, deviceId = self.check_for_dmi(sock, sock_addr)

            if isTrusted:

                if sock_addr[0] not in c.oss_seen_devices:

                    c.oss_seen_devices_lck.acquire()

                    try:
                        c.oss_seen_devices[sock_addr[0]] = {'attempt': 1, 'rebooted': False, 'socket': sock}
                    finally:
                        c.oss_seen_devices_lck.release()

                    thr = threading.Thread(target=self.first_attempt, args=(sock, sock_addr,))
                    thr.start()

                elif sock_addr[0] in c.oss_seen_devices and c.oss_seen_devices[sock_addr[0]]['attempt'] == 1 and not \
                        c.oss_seen_devices[sock_addr[0]]['rebooted']:

                    c.oss_seen_devices_lck.acquire()

                    try:
                        c.oss_seen_devices[sock_addr[0]]['attempt'] = c.oss_seen_devices[sock_addr[0]][
                                                                          'attempt'] + 1
                        c.oss_seen_devices[sock_addr[0]]['socket'] = sock
                    finally:
                        c.oss_seen_devices_lck.release()

                    thr = threading.Thread(target=self.second_attempt, args=(sock, sock_addr, deviceId,))
                    thr.start()

                else:
                    self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, sock_addr[0],
                                                           logmsg.OSSH_CONN_LIMIT.format(sock_addr[0])))
                    sock.close()
            else:
                self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, sock_addr[0], logmsg.OSSH_ERROR_VERIFY))
                sock.close()

    def first_attempt(self, conn, conn_addr):

        self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_CONN_ATTEMPT.format(
            c.oss_seen_devices[conn_addr[0]]['attempt'],
            conn_addr)))
        try:

            transport = paramiko.Transport(conn)
            transport.connect(username=c.conf.YAPT.DeviceUsr,
                              password=Tools.get_password(pwd_type=c.YAPT_PASSWORD_TYPE_DEVICE))

            with SCPClient(transport=transport) as scp:
                scp.put(c.conf.SERVICES.Ossh.LocalConfigFile,
                        remote_path=c.conf.SERVICES.Ossh.RemoteConfigFile)

            transport.close()
            conn.close()

        except (BadHostKeyException, AuthenticationException, SSHException) as e:
            self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0],
                                                   logmsg.OSSH_FILE_PROV_FAILED.format(conn_addr[0], e.message)))
            self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_CLOSE_CONN))
            conn.close()
            c.oss_seen_devices_lck.acquire()

            try:
                del c.oss_seen_devices[conn_addr[0]]
            finally:
                c.oss_seen_devices_lck.release()

            return

    def second_attempt(self, conn, conn_addr, deviceId):

        self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_CONN_ATTEMPT.format(
            c.oss_seen_devices[conn_addr[0]]['attempt'], conn_addr)))

        sample_device = self._source_plugin.run_normalizer(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), device=conn_addr[0])
        sample_device.deviceConnection = conn.fileno()
        sample_device.deviceOsshId = deviceId

        message = AMQPMessage(message_type=c.AMQP_MSG_TYPE_DEVICE_ADD,
                              payload=sample_device,
                              source=c.AMQP_PROCESSOR_SVC)
        self._source_plugin.send_message(message=message)

    def check_for_dmi(self, conn, conn_addr):

        """
        Verify MSG-ID, DeviceID and HMAC. If one of the three doesn't match close connection.
        Otherwise go ahead with provisioning steps.
        MSG-ID: DEVICE-CONN-INFO
        MSG-VER: V1
        DEVICE-ID: abc123
        HOST-KEY: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDhMc83Qp9ogdGNYJGMjjUfbCAFXspkUPrrcdEI9JgIsng3fbtZl6pSi7xyFYlZrPor' \
               '/oiNoCxQl+HOArESS+HTjFsd0tgBUyuO+rx53+vtZJ2HarsgZg59F5BjYDQq/ulCBjRDM7BQ2xViItTAIV8Q5nnikaA+mBxnNN/2EEE' \
               'huXekyibdwDY0z3X4Tc4los2qZaZBVkKeaJ6voj+7dWG8vRQINs+gXfL+jk2Lz4m72zA6y3n7KCcG4lCH3e1C1bdnSX5dblYuEUsCV' \
               '9XKbNl5qqajDeUaKeCMsjMlmXS7+E+C2pTE/Dir7T9IfN7SEpd3nDjH7fDthKKP9GCq9Lkv
         HMAC: 7aa4440cc6a8fd12bc9f13ad1af8a28ea6cc1137'
         SSH Banner:
         We want MSG-ID, MSG-VER, DEVICE-ID, HOST-KEY and HMAC

        :param conn:
        :return:
        """

        dmi = dict()
        msg = ''
        count = 5

        while len(msg) < 1024 and count > 0:
            c_recv = conn.recv(1)
            c_recv = c_recv.decode()

            if c_recv == '\r':
                continue

            if c_recv == '\n':
                count -= 1
                if msg.find(':'):
                    (key, value) = msg.split(': ')
                    dmi[key] = str(value)
                    msg = ''
            else:
                msg += c_recv

        dmi['HOST-KEY'] = dmi['HOST-KEY'].strip('\x00')

        if dmi:

            if dmi['MSG-ID'] == c.DMI_MSGID:

                self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_DMI_RECEIVED))

                if 'HMAC' in dmi:
                    lhmac = hmac.new(key=Tools.get_password(c.YAPT_PASSWORD_TYPE_OSSH), msg=dmi['HOST-KEY'],
                                     digestmod=hashlib.sha1).hexdigest()

                    if hmac.compare_digest(dmi['HMAC'], lhmac):
                        self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0],
                                                               logmsg.OSSH_HMAC_VERIFY.format('Good')))
                        return True, dmi['DEVICE-ID']
                    else:
                        self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0],
                                                               logmsg.OSSH_HMAC_VERIFY.format('Failed')))
                        conn.close()
                        return False, None
                else:
                    self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_HMAC_EMPTY))
                    conn.close()
                    return False, None

            else:
                self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_BAD_DMI))
                conn.close()
                return False, None

        else:
            self._logger.info(Tools.create_log_msg(logmsg.OSSH_SERVICE, conn_addr[0], logmsg.OSSH_BAD_DMI))
            conn.close()
            return False, None
