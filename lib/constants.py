# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar

import logging
import threading
import collections

####################
# Global variables #
####################

# Constants reflect UI related actions
UI_ACTION_UPDATE_STATUS = 'updateStatus'
UI_ACTION_ADD_DEVICE = 'addDevice'
UI_ACTION_DEL_DEVICE = 'delDevice'
UI_ACTION_UPDATE_DEVICE = 'updateDevice'
UI_ACTION_UPDATE_TASK_STATE = 'updateDeviceTaskState'
UI_ACTION_UPDATE_DEVICE_AND_RESET_TASK = 'updateDeviceAndResetTask'
UI_ACTION_UPDATE_LOG_VIEWER = 'updateLogViewer'
UI_ACTION_INIT_LOG_VIEWER = 'initLogViewer'

# Constants reflect device's status
DEVICE_STATUS_INIT = 'device_status_init'
DEVICE_STATUS_NEW = 'device_status_new'
DEVICE_STATUS_EXISTS = 'device_status_exists'
DEVICE_STATUS_CHANGED = 'device_status_changed'
DEVICE_STATUS_DONE = 'device_status_done'
DEVICE_STATUS_FAILED = 'device_status_failed'
DEVICE_STATUS_REBOOTED = 'device_status_rebooted'
DEVICE_STATUS_PROGRESS = 'device_status_progress'
DEVICE_STATUS_NEXT_TASK = 'device_status_next_task'
DEVICE_STATUS_TASK_CHANGED = 'device_status_task_changed'

# AMQP constants for all processors
AMQP_RPC_BACKEND_QUEUE = 'rpc_backend_q'
AMQP_RPC_SERVICE_QUEUE = 'rpc_service_q'
AMQP_RPC_DISTRIBUTED_QUEUE = 'rpc_distributed_q'

# AMQP processor names
AMQP_PROCESSOR_TASK = 'taskprocessor'
AMQP_PROCESSOR_UI = 'uiprocessor'
AMQP_PROCESSOR_BACKEND = 'backendprocessor'
AMQP_PROCESSOR_SVC = 'serviceprocessor'
AMQP_PROCESSOR_VERFIY = 'verifyprocessor'
AMQP_PROCESSOR_DIST = 'distprocessor'
AMQP_PROCESSOR_REST = 'restprocessor'

# AMQP message constants
AMQP_MSG_TYPE_DEVICE_ADD = 'device_add'
AMQP_MSG_TYPE_DEVICE_GET_BY_SN = 'device_get_by_sn'
AMQP_MSG_TYPE_DEVICE_UPDATE = 'device_update'
AMQP_MSG_TYPE_DEVICE_DELETE = 'device_delete'
AMQP_MSG_TYPE_DEVICE_VERIFY = 'device_verify'
AMQP_MSG_TYPE_DEVICE_UPDATE_TASK_STATE = 'device_updateTaskState'
AMQP_MSG_TYPE_REST_SITE_ADD = 'rest_site_add'
AMQP_MSG_TYPE_REST_SITE_DEL = 'rest_site_del'
AMQP_MSG_TYPE_REST_SITE_GET_ALL = 'rest_site_get_all'
AMQP_MSG_TYPE_REST_SITE_GET_BY_ID = 'rest_site_get_by_id'
AMQP_MSG_TYPE_REST_ASSET_ADD = 'rest_asset_add'
AMQP_MSG_TYPE_REST_ASSET_GET_BY_SERIAL = 'rest_asset_get_by_serial'
AMQP_MSG_TYPE_REST_ASSET_GET_BY_SITE = 'rest_asset_get_by_site'
AMQP_MSG_TYPE_REST_ASSET_UPDATE = 'rest_asset_update'
AMQP_MSG_TYPE_REST_DEVICE_GET_ALL = 'rest_device_get_all'
AMQP_MSG_TYPE_REST_DEVICE_CFG_ADD = 'rest_device_cfg_add'
AMQP_MSG_TYPE_REST_DEVICE_GET_CFG_BY_SERIAL = 'rest_device_get_cfg_by_name'
AMQP_MSG_TYPE_REST_DEVICE_GET_CFG_ALL = 'rest_device_get_cfg_all'
AMQP_MSG_TYPE_REST_DEVICE_CFG_UPDATE = 'rest_device_cfg_update'
AMQP_MSG_TYPE_REST_DEVICE_CFG_DEL = 'rest_device_cfg_del'
AMQP_MSG_TYPE_REST_GROUP_ADD = 'rest_group_add'
AMQP_MSG_TYPE_REST_GROUP_GET_BY_NAME = 'rest_group_get_by_name'
AMQP_MSG_TYPE_REST_GROUP_GET_ALL = 'rest_group_get_all'
AMQP_MSG_TYPE_REST_GROUP_UPDATE = 'rest_group_update'
AMQP_MSG_TYPE_REST_GROUP_DEL = 'rest_group_del'
AMQP_MSG_TYPE_REST_TEMPLATE_ADD = 'rest_template_add'
AMQP_MSG_TYPE_REST_TEMPLATE_GET_BY_NAME = 'rest_template_get_by_name'
AMQP_MSG_TYPE_REST_TEMPLATE_GET_ALL = 'rest_template_get_all'
AMQP_MSG_TYPE_REST_TEMPLATE_UPDATE = 'rest_template_update'
AMQP_MSG_TYPE_REST_TEMPLATE_DEL = 'rest_template_del'
AMQP_MSG_TYPE_REST_IMAGE_ADD = 'rest_image_add'
AMQP_MSG_TYPE_REST_IMAGE_GET_BY_NAME = 'rest_image_get_by_name'
AMQP_MSG_TYPE_REST_IMAGE_GET_ALL = 'rest_image_get_all'
AMQP_MSG_TYPE_REST_IMAGE_UPDATE = 'rest_image_update'
AMQP_MSG_TYPE_REST_IMAGE_DEL = 'rest_image_del'
AMQP_MSG_TYPE_REST_SVC_GET_BY_NAME = 'rest_service_get_by_name'
AMQP_MSG_TYPE_REST_SVC_GET_ALL = 'rest_service_get_all'
AMQP_MSG_TYPE_REST_SVC_UPDATE = 'rest_service_update'
AMQP_MSG_TYPE_REST_SVC_START = 'rest_service_start'
AMQP_MSG_TYPE_REST_SVC_STOP = 'rest_service_stop'
AMQP_MSG_TYPE_REST_SVC_RESTART = 'rest_service_restart'
AMQP_MSG_TYPE_REST_VAL_GET_ALL = 'rest_validation_get_all'
AMQP_MSG_TYPE_REST_VAL_VAL_ADD = 'rest_validation_add'
AMQP_MSG_TYPE_REST_VAL_VAL_DEL = 'rest_validation_del'
AMQP_MSG_TYPE_UI_UPDATE_AND_RESET = 'ui_updateAndReset'
AMQP_MSG_TYPE_UI_UPDATE_AND_REBOOT = 'ui_updateAndReboot'
AMQP_MSG_TYPE_UI_UPDATE_LOG_VIEWER = 'update_log_viewer'
AMQP_MSG_TYPE_RESPONSE = 'response'
AMQP_MSG_TYPE_REST_LOG_GET = 'rest_log_get'
AMQP_MSG_TYPE_SVC_OSSH_CLOSE_SOCKET = 'oss_close_socket'
AMQP_MSG_TYPE_SVC_PHS_VALIDATE = 'phs_validate'


# Service status
SVC_INIT = 'svc_init'
SVC_STARTED = 'svc_started'
SVC_STOPPED = 'svc_stopped'

# Web service configuration files
SVC_WEBHOOK_PATH = 'conf/services/webhook/'
SVC_PHS_CONF = 'conf/services/phs/phs.conf'
SVC_WEBHOOK_CONF = 'conf/services/webhook/webhook.conf'
SVC_UI_CONF =  'conf/yapt/ui.conf'
SVC_REST_CONF = 'conf/yapt/api.conf'
SVC_OOBA_CONF = 'conf/yapt/ooba.conf'

# Task plugin directories
TASK_PLG_PYEZ_DIRS = ['lib/tasks/provision/pyez', 'lib/tasks/provision/external', 'lib/tasks/verification']
TASK_PLG_NAPALM_DIRS = ['tasks/provision/napa', 'tasks/provision/external', 'tasks/verification']
TASK_PROV_PLG_DIRS = ['lib/tasks/provision', 'lib/tasks/provision/external']
TASK_VERI_PLG_DIRS = ['lib/tasks/verification']

# Task types
TASK_TYPE_PROVISION = 'provision'
TASK_TYPE_VERIFICATION = 'verification'

# Task states
TASK_STATE_INIT = 'task_state_init'
TASK_STATE_DONE = 'task_state_done'
TASK_STATE_FAILED = 'task_state_failed'
TASK_STATE_WAIT = 'task_state_wait'
TASK_STATE_REBOOTING = 'task_state_rebooting'
TASK_STATE_PROGRESS = 'task_state_progress'

# Task state common messages
TASK_STATE_MSG_INIT = 'Init'
TASK_STATE_MSG_DONE = 'Done'
TASK_STATE_MSG_FINAL = 'Final'
TASK_STATE_MSG_FAILED = 'Failed'
TASK_STATE_MSG_WAIT = 'Waiting'
TASK_STATE_MSG_ABORTED = 'Aborted'
TASK_STATE_MSG_OSSH_REBOOT = 'Reboot (OSSH)'

# Here we define 'keys' in dict 'shared', which are being used across tasks
TASK_SHARED_DEV_CONN = 'deviceConnection'
TASK_SHARED_STATE = 'taskState'
TASK_SHARED_IPAM = 'ipam'
TASK_SHARED_PROGRESS = 'taskProgress'
TASK_SHARED_TICKET = 'ticket'

# SRC is instance of SpaceRestConnector
SRC = None
SRC_RESPONSE_FAILURE = 'failure'

YAPT_LOGGER_FILE = 'conf/yapt/logging.yml'
YAPT_LOGGER_LEVEL_INFO = logging.INFO
YAPT_LOGGER_LEVEL_DEBUG = logging.DEBUG
YAPT_MASTER_KEY_FILE = 'conf/yapt/masterkey.yml'
YAPT_MASTER_KEY_SEED = None
YAPT_PASSWORD_TYPE_OSSH = 'ossh'
YAPT_PASSWORD_TYPE_DEVICE = 'device'
YAPT_PASSWORD_TYPE_DEVICE_RSA = 'device_rsa'
YAPT_PASSWORD_TYPE_SPACE = 'space'
YAPT_PASSWORD_TYPE_AMQP = 'amqp'
YAPT_DEVICE_DRIVER_PYEZ = 'pyez'
YAPT_DEVICE_DRIVER_NAPALM = 'napa'
YAPT_CONF_FILE = 'conf/yapt/yapt.yml'

# Storage plugins lookup type
CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG = 'get_device_data'
CONFIG_LOOKUP_TYPE_GET_DEVICE_CFG_FILE = 'get_device_file'
CONFIG_LOOKUP_TYPE_ADD_DEVICE_CFG = 'add_device_data'
CONFIG_LOOKUP_TYPE_DEL_DEVICE_CFG = 'del_device_data'
CONFIG_LOOKUP_TYPE_GET_GROUP = 'get_group_data'
CONFIG_LOOKUP_TYPE_GET_GROUP_FILE = 'get_group_file'
CONFIG_LOOKUP_TYPE_ADD_GROUP = 'add_group_data'
CONFIG_LOOKUP_TYPE_DEL_GROUP = 'del_group_data'
CONFIG_LOOKUP_TYPE_GET_TEMPLATE = 'get_template_data'
CONFIG_LOOKUP_TYPE_GET_TEMPLATE_FILE = 'get_template_file'
CONFIG_LOOKUP_TYPE_ADD_TEMPLATE = 'add_template_data'
CONFIG_LOOKUP_TYPE_DEL_TEMPLATE = 'del_template_data'
CONFIG_LOOKUP_TYPE_TEMPLATE_BOOTSTRAP = 'get_template_bootstrap_data'

# PHS related stuff
PHS_INIT_URL = '/restconf/data/juniper-zerotouch-bootstrap-server:devices/device={uid}'
PHS_NOTIFICATION_URL = '/restconf/data/juniper-zerotouch-bootstrap-server:devices/device={uid}/notification'
PHS_NOTIFICATION_CONF_APPLIED = 'configuration-applied'
PHS_NOTIFICATION_CONF_FAILED = 'configuration-failed'
PHS_NOTIFICATION_BOOTSTRAP_COMPLETED = 'bootstrap-complete'
PHS_NOTIFICATION_BOOTSTRAP_FAILED = 'bootstrap-failed'

# Space Discovery stuff
SPACE_DISCOVERY_NODS = 'Discovery succeeded'
SPACE_DISCOVERY_NOADF = 'Add Device failed'
SPACE_DISCOVERY_NOAM = 'Already Managed'
SPACE_DISCOVERY_NOS = 'Skipped'

# Source Plugin related stuff
SERVICEPLUGIN_OSSH = 'ossh'
SERVICEPLUGIN_PHS = 'phs'
SERVICEPLUGIN_TFTP = 'tftp'
SERVICEPLUGIN_DHCP = 'dhcp'
SERVICEPLUGIN_WEBHOOK = 'webhook'

# Config types
CONFIG_TYPE_MAIN = 'MAIN'
CONFIG_TYPE_GROUP = 'GROUP'

# VNF Types
VNF_TYPE_JUNIPER = 'juniper'
VNF_TYPE_OTHER = 'other'

# Config file suffix
CONFIG_FILE_SUFFIX_DEVICE = '.yml'
CONFIG_FILE_SUFFIX_GROUP = '.yml'
CONFIG_FILE_SUFFIX_TEMPLATE = '.j2'

# OSSH DMI MSG ID
DMI_MSGID = 'DEVICE-CONN-INFO'

# Port Forwarding SSHD standard path used if not OSSH
SSHD_PORT_FWD_PATH = '/var/etc/sshd_conf'

# Yapt main config view
conf = None

# lrr_counter is used Junos Space HornetQ name generation. Each device will get it's own queue.
lrr_counter = 0
lrr_lock = threading.Lock()

# Factory Containers

fc = None

# Task queue

taskq = None

# OSSH service maintains a list of already seen devices. After second connection attempt no new connection will be
# accpted by OSS service for particular IP. oss_seen_devices keeps track of device IPs. At the end of task processing, cleanup
# task will delete IP from oss_seen_devices.
oss_seen_devices = dict()
oss_seen_devices_lck = threading.Lock()

# logger stuff
#FIRST_PAD = 18
FIRST_PAD = 22
SECOND_PAD = 20
FILL_PAD = '##################'
LOGGER_SCOPE_ALL = 'logger_scope_all'
LOGGER_SCOPE_LOCAL = 'logger_scope_local'
LOGGER_LEVEL_INFO = 'info'
LOGGER_LEVEL_DEBUG = 'debug'
logger = None
active_log_plgs = collections.OrderedDict()