class LogTaskProcessor(object):
    TASKP = 'TASKPROCESSOR'
    TASKP_LOAD_TASK_SEQ = 'Loading task plugin sequence <{0}>'
    TASKP_FOUND_TASKPLG = 'Found <{0}> task plugins'
    TASKP_FOUND_PLG_ENABLED = 'Found enabled task plugin <{0}>'
    TASKP_LOADED_PLG_ENABLED = 'Loaded enabled task plugin <{0}>'
    TASKP_EXECUTED_PLG_ENABLED = 'Executed enabled task plugin <{0}>'
    TASKP_NOT_FOUND_PLG_ENABLED = 'Task plugin <{0}> not found'
    TASKP_STOP_DEV_REBOOT = 'Stop proccessing tasks since device <{0}> rebooting'
    TASKP_STOP_NO_DEVGRP = 'Can\'t find <{0} in device conf file'
    TASKP_STOP_NO_DEVGRP_CFG = 'No deivce group config found'
    TASKP_SEQ_EMPTY = 'Task sequence empty'
    TASKP_CLOSE_DEV_CONN = 'Closing device connection <{0}>'
    TASKP_STOP_VERFIY_FAILURE = 'Do not start verification for device <{0}> since task failure'
    TASKP_TASK_ERROR = 'Task before Task <{0}> has errors. Please check log'
    TASKP_DEVICE_STATUS_ERR = 'Error with device status <{0}>'
    TASKP_DEFECT_MSG = 'Received defect message'
    TASKP_GROUP_CFG_NOK = 'Error in getting device group config <{0}>'
    TASKP_CONN_ERR_CLOSE = 'Error in closing connection for device {0} with error: {1}'


class LogInitTask(object):
    INIT_EXTEND_CFG = 'Extending device connection object to support configuration tasks'
    INIT_EXTEND_SW = 'Extending device connection object to support software tasks'
    INIT_EXTEND_SW_NOK = 'Failed extending connection object for device type <NFX> to support software tasks'
    INIT_DEV_CONN_NOK = 'Failed to open connection to device <{0}> (Check username and password)'


class LogSoftwareTask(object):
    SW_START_UPDATE = 'Start image provisioning process for device <{0}>'
    SW_NO_UPDATE_NEEDED_SAME = 'No update needed (Same Version)'
    SW_NO_UPDATE_NEEDED_NEWER = 'No update needed (Device Version newer)'
    SW_NO_TARGET_VERS_FOUND = 'Target version value for device model <{0}> not found'
    SW_UPDATE_NEEDED = 'We need to update. Device version <{0}> / Target version <{1}>'
    SW_INSTALL_VERS = 'Installing software version <{0}>'
    SW_CLEANUP_STORAGE = 'Cleaning up storage'
    SW_COPY_IMG = 'Copy image...'
    SW_COPY_IMG_NOK = 'File copy failed with error <{0}>'
    SW_INSTALLED_VERS = 'Installed Version is: <{0}>'
    SW_TARGET_VERS = 'Target Version is: <{0}>'
    SW_INSTALL_OK = 'Software installation succeeded for device <{0}>'
    SW_INSTALL_NOK = 'Software installation failed with error <{0}>'
    SW_CONN_NOK = 'Connection error for device <{0}>'
    SW_IMG_NOK = 'No image file found for target version <{0}>'
    SW_IMG_VALUE_NOK = 'No target version value found in group configuration <{0}>'
    SW_REBOOT = 'Initiating reboot for device <{0}>'
    SW_REBOOT_DEV_RESP = '{0}'
    SW_CONN_LOOSE_REBOOT = 'About to loose connection...'
    SW_PROBE_DEV = 'Probing device is alive in <{0}> seconds interval'
    SW_PROBE_DEV_NOK = 'Device <{0}> still not rebooted after <{1}> probing attempts'
    SW_PROBE_WAIT_REBOOT = 'Waiting for device rebooting...: {0}'
    SW_PROBE_WAKEUP = 'Please give device <{0}> some time to wake-up...'
    SW_PROBE_WAKUP_OK = 'Connecting to device <{0}> now...'
    SW_CONN_OK = 'Successfully connected to device <{0}>'
    SW_DONE_SAME_VERS = 'Done (same version)'
    SW_DONE_DEV_NEWER_VERS = 'Done (device newer)'

class LogFilecpTask(object):
    CP_INIT = 'Start file provisioning process for file(s) <{0}>'
    CP_COPY = 'Copy file <{0}> to device'
    CP_SUCCESS = 'File provisioning process for file <{0}> successful'
    CP_FAILED = 'File provisioning failed. Reason <{0}>'
    CP_FAILED_NO_CONN = 'File provisioning failed. No Connection to device'


class LogConfigurationTask(object):
    CONF_TASK_INIT = 'Start config provisioning process for device <{0}>'
    CONF_TASK_LOCK = 'Locking device configuration'
    CONF_TASK_LOCK_OK = 'Successfully locked device configuration'
    CONF_TASK_LOCK_NOK = 'Unable to lock configuration. Reason: {0}'
    CONF_TASK_LOAD = 'Loading configuration changes'
    CONF_TASK_LOAD_NOK = 'Unable to load configuration changes. Reason: {0}'
    CONF_TASK_UNLOCK = 'Unlocking device configuration'
    CONF_TASK_UNLOCK_OK = 'Successfully unlocked device configuration'
    CONF_TASK_UNLOCK_NOK = 'Unable to unlock device configuration'
    CONF_TASK_COMMIT = 'Committing configuration'
    CONF_TASK_COMMIT_NOK = 'Unable to commit configuration. Reason: {0}'
    CONF_TASK_COMMIT_OK = 'Configuration file <{0}> committed on device'
    CONF_TASK_CONN_NOK = 'No connection to device <{0}>'
    CONF_TASK_CFG_TEMPLATE_ERROR = 'Template error({1}): {2} --> {3}'
    CONF_TASK_CFG_DEV_DATA_ERROR = 'Error in reading device data'


class LogRuleTask(object):
    RULE_FILE_NOK = 'Failed to open file <{0}> with error: {1}'
    RULE_INIT_NOK = 'Junos Space add policy rule add process failed for device <{0}>. Reason: {1}, {2}'


class LogAssignTask(object):
    ASSIGN_INIT = 'Start Junos Space device to policy assign process for device: <{0}>'
    ASSIGN_DONE = 'Assign policy object <{0}> to device <{1}> successful'
    ASSIGN_TEMPLATE_FILE_NOK = 'Failed to open template file <{0}> with error: {1}'


class LogDiscoveryTask(object):
    DISCOVERY_MODE_NOK = 'Unknown discovery mode <{0}>'


class LogAnsibleTask(object):
    ANSIBLEAPI = 'ANSIBLEAPI'
    ANSIBLE_ERROR = 'Error in playbook tasks'
    PLAYBOOK_NOT_FOUND = 'Playbook not found. Reason: <{0}>'
    PLAYBOOK_FINISHED_SUCCESS = 'Finished all playbook tasks successfully'
    PLAYBOOK_ERROR = 'Error in playbook task <{0}>'
    PLAYBOOK_TASK_ERROR = '<{0}> failed'
    PLAYBOOK_TASK_OK = '<{0}> ok'
    ERROR_UNREACHABLE = '<{0}> unreachable'
    ERROR_DEV_CFG_FILE = 'Error in reading device config files'


class Logvnfstage(object):
    VNFSTAGE_SETUP_DIR = 'Setting up directories'
    VNFSTAGE_CP_BASE_IMG = 'Copy base image {0} to {1}:{2}'
    VNFSTAGE_CP_BASE_IMG_OK = 'Base image copy process for VNF <{0}> successful'
    VNFSTAGE_GEN_BOOTSTRAP = 'Generate bootstrap config for VNF <{0}>'
    VNFSTAGE_CP_ERR = '<{0}> <{1}>:<{2}>'
    VNFSTAGE_DEV_CONF_READ_ERR = 'Error reading device configuration'
    VNFSTAGE_COPY_BOOTSTRAP = 'Copy bootstrap config <{0}> to {1}:{2}'
    VNFSTAGE_COPY_BOOTSTRAP_OK = 'Bootstrap copy process for VNF <{0}> successful'
    VNFSTAGE_MAKE_CP_BASE_IMG = 'Make copy of base image for VNF <{0}>'
    VNFSTAGE_MAKE_CP_BASE_IMG_OK = 'Making copy of base image for VNF <{0}> successful'
    VNFSTAGE_GEN_ISO = 'Generating bootstrap iso image for VNF <{0}>'
    VNFSTAGE_BOOSTRAP_OK = 'Bootstrap provisioning process for VNF <{0}> successful'


class Logvnfspin(object):
    VNFSPIN_INIT = 'Starting spinup process for VNF <{0}>'
    VNFSPIN_VNF_OK = 'Spinup process for VNF <{0}> successful'
    VNFSPIN_FILE_ERR = 'Error reading device config data'


class Logipam(object):
    IPAM_CONN_ERR = 'Error in connecting to IPAM server <{0}>'
    IPAM_PREFIX_OK = 'Success in getting prefix from <{0}>'
    IPAM_PREFIX_ERR = '<{0}>'
    IPAM_PREFIX_FULL = 'No more prefixes available in <{0}>'


class LogPolicyTask(object):
    POLICY_INIT = 'Start Junos Space add policy process for device <{0}>'
    POLICY_CREATE_NOK = 'Junos Space add policy process for device <{0}> failed. Reason: {1}, {2}'
    POLICY_UNKNOWN_CODE = 'Unknown repsone code <{0}>'
    POLICY_TEMP_FILE_NOK = 'Failed loading template <{0}> with error <{1}>'


class LogCertTask(object):
    CERT_FILE_OK = 'File provisioning process for device <{0}> successful'
    CERT_DEV_DATA_NOK = 'Error in reading device data'
    CERT_ISSUE_CMD = 'Issue command: <{0}>'
    CERT_ISSUE_CMD_RESP = 'Issue command response: <{0}> --> <{1}>'
    CERT_ISSUE_CMD_NOK = 'Executing command <{0}> failed with error <{1}>'


class LogCleanupTask(object):
    CLEANUP_CLOSE_CONN = 'Closing device connection <{0}>'
    CLEANUP_CLOSE_CONN_SUCCESS = 'Successfully closed device connection <{0}>'
    CLEANUP_CLOSE_CONN_ERROR = 'Error closing Device %s connection <{0}>'
    CLEANUP_CLOSE_CONN_TIMEOUT = 'Timeout error'


class LogTicketTask(object):
    TICKET_INIT = 'Start ticket provisioning process for device <{0}> in <{1}> mode'
    TICKET_CONN_INIT = 'Connecting to ticketing system <{0}>'
    TICKET_CONN_OK = 'Successfully connected to ticketing system <{0}>'
    TICKET_CONN_NOK = 'Failed to connect to ticketing system <{0}> with error <{1}>'
    TICKET_CREATE_OK = 'Successfully created ticket <{0}>'
    TICKET_CREATE_NOK = 'Failed to create ticket with error <{0}>'
    TICKET_UPDATE_OK = 'Successfully updated ticket <{0}>'
    TICKET_UPDATE_NOK = 'Failed to update ticket <{0}> with error <{1}>'
    TICKET_TEMPLATE_ENV_NOK = 'Failed to get ticket tempalte file directory <{0}>'


class Logfile(object):
    FILESVC = 'FILESERVICE'
    FILESVC_INIT = 'Starting file service...'
    FILESVC_WATCHED_DIR = 'watched_dir = {0}'
    FILESVC_PATTERN = 'patterns = {0}'
    FILESVC_MODIFIED = 'File {0} was modified. Watching for new devices...'


class Logossh(object):
    OSSH_SERVICE = 'OSSHSERVICE'
    OSSH_LISTEN = 'Listening for new connections...'
    OSSH_START = 'Starting OSSH service...'
    OSSH_BIND_FAILED = 'Bind failed <{0}> '
    OSSH_BIND_FAILED_1 = 'Seems to be another YAPT instance is already running or interface not available to bind to'
    OSSH_LISTEN_FAILED = 'Listen failed <{0}>'
    OSSH_NEW_CONN = 'New connection from <{0}>'
    OSSH_DMI_RECEIVED = 'Received DMI DEVICE-CONN-INFO request'
    OSSH_HMAC_VERIFY = 'HMAC verification <{0}>'
    OSSH_CONN_ATTEMPT = '<{0}> connection attempt from device <{1}>'
    OSSH_FILE_PROV_FAILED = 'File provisioning for device <{0}> failed. Reason <{1}>'
    OSSH_CLOSE_CONN = 'Closing device connection'
    OSSH_CONN_LIMIT = 'To many connection attempts from <{0}>. Closing connection'
    OSSH_ERROR_VERIFY = 'Error in device verification. Closing connection'
    OSSH_HMAC_EMPTY = 'Received empty HMAC. Closing connection'
    OSSH_BAD_DMI = 'Received bad DMI request. Closing connection'


class Logphs(object):
    PHS_SERVICE = 'PHSSERVICE'
    PHS_LISTEN = 'Listening for new connections...'
    PHS_START = 'Starting Phone Home Server...'
    PHS_STAGE1_SUCCESS = 'The stage1 configuration is successfully committed on device <{0}>'
    PHS_STAGE1_FAILED = 'The stage1 configuration failed to commit on device: <{0}>'
    PHS_BOOTSTRAP_SUCCESS = 'Bootstrapping device <{0}> successful'
    PHS_BOOSTRAP_FAILED = 'Bootstrapping device <{0}> failed'
    PHS_BOOSTRAP_FILE_FAILED = 'Can\'t find boostrap file <{0}>'
    PHS_DEV_CONF_FAILED = 'Can\'t get device config data'
    PHS_SEC_SVC = '{0} activated as second service. Waiting for incoming device {1} connection...'
    PHS_TEMPLATE_ERROR = 'Template error({0}): {1} --> {2}'
    PHS_CONF_KEY_ERROR = 'Can\'t find key <{0}> in device config file'
    PHS_VALIDATION_SUCCESS = 'Validation successful for device <{0}>'
    PHS_VALIDATION_FAILED = 'Validation failed for device <{0}>'
    PHS_SSL_ENABLED = 'SSL Enabled'
    PHS_SSL_NO_CERT = 'No certificate file found'
    PHS_SSL_NO_KEY = 'No private key file found'


class LogPlgFactory(object):
    SRCPLG = 'SOURCEPLG'
    SRCPLG_FOUND = 'Found source plugin <{0}>'
    SRCPLG_LOAD_CFG = 'Loading source plugin configuration: {0}'
    SRCPLG_LOAD_PLG = 'Loading source plugin <{0}>'
    SRCPLG_SEARCH = 'Searching for source plugin <{0}>'
    SRCPLG_FILE_ERROR = 'File error({0}): {1} --> {2}'
    SVCPLG = 'SERVICEPLUGIN'
    SVCPLG_SEARCH = 'Searching for service plugin: <{0}>'
    SVCPLG_LOAD = 'Loading service plugin: <{0}>'
    SVCPLG_NOT_FOUND = 'Service plugin <{0}> not found'
    BACKENDPLG = 'BACKENDPLG'
    BACKENDPLG_SEARCH = 'Searching for backend plugin <{0}>'
    BACKENDPLG_FOUND = 'Found backend plugin <{0}>'
    BACKENDPLG_LOAD = 'Loading backend plugin: <{0}>'
    BACKENDPLG_NOT_FOUND = 'No backend plugin found with name: {0}'
    SPACEPLG = 'JSPACEPLG'
    SPACEPLG_SEARCH = 'Searching for Junos Space plugin <{0}>'
    SPACEPLG_FOUND = 'Found Junos Space plugin <{0}>'
    SPACEPLG_LOAD = 'Loading Junos Space plugin: <{0}>'
    SPACEPLG_NOT_FOUND = 'No Junos Space plugin found with name: {0}'


class LogSqlBackend(object):
    SQLBACKEND = 'SQLBACKEND'
    SQLBACKEND_STARTED = 'SQL Backend service started...'


class LogInternalBackend(object):
    INTBACKEND = 'INTBACKEND'
    INTBACKEND_STARTED = 'INTERNAL Backend service started...'
    INTBAKCEND_TIMESTAMP_NOK = 'New device\'s timestamp should be newer then existing one'
    INTBACKEND_KEY_NOK = 'Key <{0}> does not exists in database'


class LogSpace(object):
    SPACE = 'JSPACEPLG'
    SPACEPLG_LOADED = 'Plugin <{0}> successfully loaded'
    SPACEPLG_Q_CREATED = 'Successfully created queue <{0}>'
    SPACEPLG_Q_ALREADY = 'Queue <{0}> already created'
    SPACEPLG_Q_FAILED = 'Cannot create queue <{0}>'
    SPACEPLG_CONN_NOK = 'Error connecting to <{0}>: <{1}>'
    DISCOVERY_INIT = 'Start Junos Space discovery process for device <{0}>'
    DISCOVERY_JOB = 'Change is in progress - check job ID <{0}>'
    DISCOVERY_STATE = 'Discovery state for device is <{0}>'
    DISCOVERY_CLENUP = 'Device discovery done for device <{0}>. Cleaning up queues'
    DISCOVERY_OK_SUM = 'Discovery for device <{0}> Summary <{1}>'
    DISCOVERY_JOB_CANCELED = 'Seems to be the job was canceled by Space user'
    DISCOVERY_UNKOWN_STATE = 'Got unknown Junos Space state <{0}> in response'
    DISCOVERY_UNKOWN_CODE = 'Got unknown status code <{0}> in Junos Space response'
    PUBLISH_INIT = 'Start Junos Space policy publish process for device <{0}>'
    PUBLISH_DONE = 'Publishing policy for device <{0}> done. Check Space job ID <{1}>'
    PUBLISH_NOK = 'Junos Space policy publish failed for device <{0}>, reason <{1}>'
    PUBLISH_RESP_NOK = 'Error in response from Junos Space instance <{0}><{1}>'
    PUBLISH_RESP_UNKNOWN = 'Unknown Space repsonse status <{0}>'


class LogOoba(object):
    OOBA_SN_NOT_FOUND = '<{0}> <{1}>not found in backend'
    OOBA_GROUP_FILE_OK = 'Found group config file <{0}>'
    OOBA_TEMPLATE_FILE_OK = 'Found template file <{0}>'
    OOBA_TEMPLATE_FILE_NOK = 'Missing template file <{0}>'
    OOBA_TEMPLATE_DATA_OK = 'Found template <{0}>'
    OOBA_ID_AND_FILE_NOK = 'Configuration not found for id <{0}>'
    OOBA_GROUP_CONF_NOK = 'Error in getting device group config <{0}> <{1}>'
    OOBA_BOOSTRAP_TEMPLATE_OK = 'Found bootstrap template {0}'
    OOBA_BOOSTRAP_TEMPLATE_NOK = 'Error({0}): {1} --> {2})'
    OOBA_CFG_FILE_OK = 'Found device config file <{0}>'
    OOBA_CFG_FILE_NOK = 'Missing device config file <{0}>'


class LogLocal(object):
    LOCAL_DEV_CFG_FILE_OK = 'Found device config file <{0}>'
    LOCAL_DEV_CFG_FILE_NOK = 'Missing config file <{0}>'
    LOCAL_TEMPLATE_FILE_OK = 'Found template file <{0}>'
    LOCAL_TEMPLATE_FILE_NOK = 'Missing template file <{0}>'
    LOCAL_GRP_CFG_FILE_OK = 'Found group config file <{0}>'
    LOCAL_GRP_CFG_FILE_NOK = 'Error in opening group config file <{0}>'
    LOCAL_GRP_CFG_FILE_MISS = 'Missing group config file <{0}>'

class LogGit(object):
    GIT_DEV_CFG_OK = 'Found device config file <{0}>'
    GIT_DEV_CFG_NOK = 'Missing config file for serialnumber <{0}>'
    GIT_DEV_GRP_CFG_OK = 'Found group config file <{0}>'
    GIT_DEV_GRP_CFG_NOK = 'Error in getting device group config <{0}> <{1}>'
    GIT_DEV_TEMPL_OK = ''
    GIT_DEV_TEMPL_NOK = ''

class LogTools(object):
    CONN_MGMT = 'CONNMGMT'
    CONN_MGMT_PROBING_DEV = 'Probing device <{0}> (Timeout {1} sec)'
    CONN_MGMT_PROBING_OK = 'Probing device <{0}> (Timeout {1} sec) --> OK'
    CONN_MGMT_PROBING_FAILED = 'Failed to open connection to device <{0}> (No Netconf / SSH connection. Check bootstrap config or probe timeout)'
    CONN_MGMT_OPEN_FAILED = 'Failed to open connection to device reason <{0}>'
    CONN_MGMT_DEV_DRIVER_NOK = 'Unknown device driver type'
    AMQP = 'AMQP'
    AMQP_INIT = 'Exchange --> {0}, Type --> {1}, Routing Key --> {2}, Host --> {3}, Channel --> {4}'
    YAPT_CONF = 'YAPTCONF'
    YAPT_CONF_LOAD_ERR = 'Loading YAPT config file with error <{0}:{1}>'
    YAPT_CONF_LOAD_GRP_ERR = 'Loading group file <{0}> failed with error <{1}>'


class LogTaskTools(object):
    SSHFWD = 'SSHFWD'
    SSHFWD_INIT = 'Preparing setup port forwarding: {0}:{1} --> {2}:{3}'
    SSHFWD_INIT_FAILURE = 'Error in port forward request <{0}>'
    SSHFWD_REQ_FAILED = 'Forwarding request to {0}:{1} failed: {2}'
    SSHFWD_REQ_CONNECTED = 'Connected! Tunnel open {0} -> {1} -> {2}'
    SSHFWD_REQ_CLOSED = 'Tunnel closed from <{0}>'
    SSHFWD_CONN_NOK = 'Failed to open connection to device'
    SW_CHECK_DIR = 'Local images directory check for version <{0}>'
    SW_IMAGE_OK = 'Found proper image for target version {0}'
    SW_IMAGE_NOK = 'No image found for target version <{0}>'
    CONF_DEV_CFG = 'PREPDEVCONF'
    CONF_DEV_CFG_TEMPLATE_ERROR = 'Template error({1}): {2} --> {3}'
    CONF_DEV_CFG_DEV_DATA_ERROR = 'Error in reading device data'
    CONF_SOURCE_PLG = 'CONFSOURCE'
    CONF_SOURCE_PLG_LOAD = 'Loading config source plugins <{0}>'
    CONF_SOURCE_PLG_FOUND = 'Found enabled config source plugin <{0}>'
    CONF_SOURCE_PLG_LOADED = 'Loaded enabled config source plugin <{0}>'
    CONF_SOURCE_PLG_EXEC = 'Executed enabled config source plugin <{0}>'
    CONF_SOURCE_PLG_NOK = ''
    CONF_VALIDATE = 'CONFVALIDATE'
    CONF_VALIDATE_INIT = 'Validating <{0}> configuration'
    CONF_VALIDATE_OK = '<{0}> configuration validation successful'
    CONF_VALIDATE_NOK = '<{0}> configuration validation failed with error <{0}>'


class LogYaptOobaUi(object):
    OOBA_FILE_NOK = 'Index file not found <{0}>'


class LogYaptWebUi(object):
    WEBUI_FILE_NOK = 'Index file not found <{0}>'
    WSHDLR = 'WSHANDLER'
    WSHDLR_RCVD_DATA_NOK = 'Error in received data <{0}>'


class LogUiProcessor(object):
    UIPRO_WS_CONN_OK = 'Successfully opened websocket connection to server <{0}>'
    UIPRO_WS_CONN_NOK = 'Failed to open websocket connection to server <{0}> with <{1}>'
    UIPRO_WS_SOCK_ERR = '{0}{1}{2}{3}'
    UIPRO_WS_MSG_NOK = 'Preparing message failed. Not sending message through WS'
    UIPRO_AMQP_MSG_NOK = 'Recevied defect amqp message'


class LogAmqp(object):
    AMQP_CL_CONN_OK = 'Client <{0}> connected to WS server'
    AMQP_CL_STATUS_NOK = 'Status <{0}> not defined. Failed to prepare json data'
    AMQP_BUS_NOK = 'Error in connecting to amqp bus <{0}>'


class LogSourcePlg(object):
    OSSH_PLG = 'OSSHPLG'
    DHCP_PLG = 'DHCPPLG'
    PHS_PLG = 'PHSPLG'
    TFTP_PLG = 'TFPTPLG'
    TFTP_PLG_FILE_NOK = 'Failure in opening logfile <{0}>'
    TFTP_PLG_PARSE_NOK = 'Error in parsing data <{0}>'


class LogCommon(object):
    IS_SUBCLASS = '<{0}> Subclass <{1}>'
    IS_INSTANCE = '<{0}> Instance <{1}>'


class LogSampleDevice(object):
    SAMPLEDEV_STATUS_NOK = 'Current device status is <{0}>. Not sending update to UI'

class LogConfigSource(object):
    SOURCE_DEV_TYPE_NOK = 'Error reading device type in config source <{0}>'