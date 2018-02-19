# Introduction #

YAPT is a tool to demonstrate Juniper automation capabilities on SRX / EX / VMX / NFX platform. Zero Touch Provisioning could be demonstrated for example during customer PoC.

# Use Cases #

## Centralised Provisioning before shipment ##

During the boot sequence the device will get initial configuration parameters and connects to a centralised server that would
build and deliver a device specific configuration. The location is determined
by device's serial number. But could also be any other device specific information.

Once all provisioning / verification tasks are done, device can be shipped to it's final destination.
The ability to provision more than one device at the same time is also possible within the YAPT workflow.

## Decentralized provisioning with Phone Home ##

Device will be shipped to it's final destination.

The provisioning process consists of several tasks:
* Device calls home using Juniper redirect service pointing to YAPT
* Bootstrap config will be applied using Phone Home
* YAPT starts provisioning process

## RMA a device ##

Another use case is device replacement in case of hardware defect.
It depends on which provisioning method is being used (either Centralized or Decentralized) how the new device will be
provisioned.

# Architecture #
YAPT has a modular architecture based on plugins and a bus system.

![Image of YAPT architecture](https://github.com/Juniper/YAPT/blob/master/doc/pics/yapt_architecture.png)

## Bus ##
YAPT uses AMQP based bus for internal communication between "Processors".

## Processor ##
A processor in YAPT architecture receives / sends messages using underlaying bus. Processor starts for example a provisioning task or sends updates to WebUI. 
Source plugins are the starting point generating messages.

## Source plugins ##
A source plugin relays on a service. Currently YAPT ships with three services:
  * PHS service
       + Provision process can be triggered using Phone Home client
  * Outbound-ssh service
      + Device initiated ssh connection points to YAPT
      + Outbound-ssh plugin can be used for automatic in band certificate roll out
      + It's currently not possible to use outbound-ssh together with the software provisioning task
  * File service
      + DHCP servers log file
      + TFTP servers log file
      + Could be any file we observing for changes

A file based source plugin would use the file service which is listening for file change notifications. 
It is possible extend YAPT capabilities by adding new source plugins / services.
Another way to trigger tasks is by invoking through YAPT REST API.

## Provisioning tasks ##
Provisioning tasks are doing the work when it comes to "provisioning" the device. There are tasks for:

- Software Update
- Configuration deployment
  * Internal
    + Uses template based configuration generation
  * Ansible
    + Use Ansible API to push configs to devices
- IPAM
  * Currently supported IPAM is nipap
- File Copy (used for copying files to device)
- Inband certificate roll out 
  * Provision certificates for e.g. ADVPN / AutoVPN
- Junos Space tasks
  * Junos Space device discovery
    + Space discovers device
    + Configlet / OSSH driven on boarding
  * Junos Space SD security policy creation
  * Junos Space SD rule creation
  * Junos Space SD assign policy to device
  * Junos Space SD push changes to device
- jEDI integration
  * RT Tracker (ticket system integration)
- Gitlab CI/CD integration

It's possible to extend YAPT capabilities by adding new tasks. Tasks are worked on in a sequential order. The order can be changed.

## Verification tasks ##
Verification tasks could be used to check for certain state on the device. 
For example check if IPSec VPN tunnel and OSPF neighbours are up. 
Currently there are is only one verification task shipping with YAPT. I think this could be done better using Jsnapy or NITA.

## Backend ##
YAPT supports different backend types. Standard backend is called "internal". This backend type doesn't bring any persistence. But should be enough for PoC scenario.
YAPT also ships with SQLite based Backend which brings persistence.

## Configuration Sources ##
YAPT can pull needed configuration information from different sources. YAPT ships with following config source plugins:

- Local
  * Get device and group configs from local file system
- GitLab
  * Get device and group configs from git repository

Default source is local file system. It is also possible to build a config source chain. 
For example YAPT first will have a look at git repo and when no config found look at local file system.

## Out of band activation (OOBA) ##
In case of drop shipping devices to it's final location we need some out of band activation path. YAPT ships with an OOBA
WebUI which could demonstrate this. Since we do not know the serial number of the device we need a mapping between actual device
serial number and a so called config id. Device serial number could be scanned from device's barcode and then assign to config id using
the OOBA WebUI.  

![Image of YAPT Job Overview](https://github.com/Juniper/YAPT/blob/master/doc/pics/yapt_ooba_start_screen.png)

To use this feature we would need to create a site and assign assets to this site. Each asset maps serial number to a config id.
The config id reflects the actual config which should be pushed down to the device.   

## UI ##
There is a very simple WebUI, which gives overview of already provisioned devices and provisioning status of new devices.

![Image of YAPT Job Overview](https://github.com/Juniper/YAPT/blob/master/doc/pics/yapt_job_screen.png)

# Installation #

## Default username and password ##
- For device authentication with username/password:
  + username is `root`
  + password is `juniper123`

- For Junos Space authentication:
  + username is `rest`
  + password is `juniper123`

- For OSSH service shared secret is `juniper123`

## Requirements ##

- Hardware
  * 1 CPU
  * 1GB RAM
  * Disk space 10GB (depends on how many software image files will be saved in image directory)

## Standalone ##

To run YAPT in a standalone environment grab a CentOS 7 box and follow steps below:

- Install a CentOS 7 box
  * This box runs YAPT services later on
- Prepare your seed host (in this case a Ubuntu box)
  * Install python with `sudo apt-get install python python-pip -y`
  * Install ansible with `sudo apt-get install ansible -y`
  * Update python pip with `sudo pip install --upgrade pip`
  * Update ansible with `sudo pip install --upgrade ansible`
- Clone YAPT installer repository on your seed host with
  * `git clone https://github.com/Juniper/YAPT-docker`
- Change into directory
  * `cd yapt-docker/standalone/ansible`
- Edit the hosts inventory file and change according your environment
  * `nano inventory/hosts`
  
  
  ```
  [yapt]
  yapt-01 ansible_host=172.16.146.131 ansible_connection=ssh ansible_user=root
  ```
      
- Edit group variables file `all` and change needed setting to fit your environment
  * `nano group_vars/all`
  
  
  ```
  # Rabbitmq stuff
  rabbitmq_version: 3.6.14
  rabbitmq_user: yapt
  rabbitmq_pw: juniper123

  # DHCPD stuff
  subnet: 172.16.146.0
  mask: 255.255.255.0
  range_low: 172.16.146.100
  range_high: 172.16.146.110
  broadcast: 172.16.146.255
  option_routers: 172.16.146.2
  next_server: 172.16.146.130
  filename: init.conf

  # YAPT stuff
  githubuser:
  githubpassword:
  yapt_repo_url: github.com/Juniper/YAPT.git
  yapt_branch: master
  yapt_webui_address: 172.16.146.130
  yapt_webui_port: 8080
  ```

- Run standalone deployment with
  * `ansible-playbook -i inventory/hosts deploy-yapt-server.yml`

## Docker ##

Running YAPT in docker environment consists of following containers: 

- Backend container
- UI container
- Service container
- Bus container
- dnsmasq container
- DHCP container (not running yet)

To bring up YAPT docker environment we need following steps:

- Prepare your seed host (in this case a Ubuntu box)
  * Install python with `sudo apt-get install python python-pip -y`
  * Install ansible with `sudo apt-get install ansible -y`
  * Update python pip with `sudo pip install --upgrade pip`
  * Update ansible with `sudo pip install --upgrade ansible`
- Clone YAPT installer repository with
  * `git clone https://github.com/Juniper/YAPT-docker`
- Change into directory
  * `cd yapt-docker/docker/ansible`
- Edit the hosts inventory file and change according your environment
  * `nano inventory/hosts`
  
  ```
  [yapt]
  yapt-01 ansible_host=172.16.146.131 ansible_connection=ssh ansible_user=root
  ```
      
- Edit group variables file `all` and change needed setting to fit your environment
  * `nano group_vars/all`
  
  
  
  ```yaml
  # Rabbitmq stuff
  rabbitmq_version: 3.6.14
  rabbitmq_user: yapt
  rabbitmq_pw: juniper123

  # DHCPD stuff
  subnet: 172.16.146.0
  mask: 255.255.255.0
  range_low: 172.16.146.100
  range_high: 172.16.146.110
  broadcast: 172.16.146.255
  option_routers: 172.16.146.2
  next_server: 172.16.146.130
  filename: init.conf

  # YAPT stuff
  githubuser:
  githubpassword:
  yapt_repo_url: github.com/Juniper/YAPT.git
  yapt_branch: master
  yapt_webui_ext_ip: 172.16.146.131
  yapt_webui_port: 6580
  yapt_restapi_port: 6581
  yapt_oobaui_port: 6582
  ```
  
- Run docker deployment with
  * `ansible-playbook -i inventory/hosts deploy-yapt-server.yml`

## Vagrant ##
Below picture illustrates how Vagrant will setup YAPT topology:

![Image of YAPT Vagrant topology](https://github.com/Juniper/YAPT/blob/master/doc/pics/virtualbox_topo.png)

To install YAPT with vagrant follow following steps:

- Install Vagrant
- Install VirtualBox
- Clone YAPT installer repository with
  * `git clone https://github.com/Juniper/YAPT-docker`
- Change into directory
  * `cd yapt-docker/docker/vagrant`
- Clone YAPT repository with
  * `git clone https://github.com/Juniper/YAPT`
- Run vagrant deployment with
  * `vagrant up`
- Setup a vSRX in VirtualBox
  * <https://github.com/Juniper/YAPT/blob/master/doc/presentation/yapt_quick_start.pptx>

## EDI ##

To install YAPT to integrate into j-EDI we need to:
- Setup j-EDI environment <https://github.com/Juniper/jedi-seed/blob/master/README.md>
- Setup the YAPT EDI plugin: <https://github.com/Juniper/j-EDI/blob/master/saltstack/srv/plugins/yapt/README.md> 

Current integration is with RT ticketing system. We could demonstrate updating a ticket with provisioning / verification task information.   
For more information about YAPT provisioning task plugin have a look at the task plugin section.

## Standalone from source / scratch ##

To run YAPT in standalone mode we need a linux box. I did the setup with a CentOS 6/7 and Ubuntu 16.04
Here are the steps to prepare a CentOS 6/7 based box:

```
yum install python-devel libxml2-devel libxslt-devel gcc openssl libffi-devel wget curl
yum groupinstall "Development tools"
yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel socat dhcp dnsmasq

cd /usr/src
wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz
tar xzf Python-2.7.13.tgz
cd Python-2.7.13
./configure
make altinstall

cd /tmp
wget https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.9/rabbitmq-server-3.6.9-1.el7.noarch.rpm
rpm --import https://www.rabbitmq.com/rabbitmq-release-signing-key.asc
rpm -ivh rabbitmq-server-3.6.9-1.noarch.rpm

nano /etc/rabbitmq/rabbitmq.config

[
    {rabbit, [{tcp_listeners, [5672]}, {heartbeat, 0}]}
].

git clone https://git.juniper.net/cklewar/yapt.git
cd juniper-yapt-__<VERSION>__
pip install -r requirements.txt

Check if Python2.7 has ssl support:

/usr/local/bin/python2.7

If you see error below than no ssl support which is mandatory. Check if needed libs are installed e.g. openssl-devel.

>>> import ssl
Traceback (most recent call last):
 File "<stdin>", line 1, in ?
ImportError: No module named ssl
>>>

```

Shown Rabbitmq config will not work with version >= 3.7.0.


### Configuration steps ###

- Create AMQP bus user and password

  * Start rabbitmq server using linux specific start scripts. "/etc/init.d/rabbitmq-server start on CentOS 6"
  * rabbitmqctl add_user yapt juniper123
  * rabbitmqctl set_user_tags yapt administrator
  * rabbitmqctl set_permissions -p / yapt ".*" ".*" ".*"

- Edit __conf/yapt/yapt.yml__ file to fit your environment settings
  - Parameter __SourcePlugins__: Set the source plugin(s) to be used and configure service settings under __SERVICES Section__
  - Parameter __WebUiAddress__: should be set to interface IP WebUI will be reachable
  - If YAPT server operates behind NAT / Proxy we need to set:

  
  ```
  WebUiNat: False                                 #Enable YAPT WebUI being behind NAT
  WebUiNatIp: 172.30.162.52                       #NAT IP
  ```

- Configure the services which have been enabled under __SourcePlugins__ section

# Configuration #

## Main Config ##

All settings in this file have a global scope.
YAPT main config file `conf/yapt/yapt.yml` consists of following sections:

### Section: YAPT ###

  - SourcePlugins: Enable source plugins and their respective service
    + Currently YAPT ships with `phs, ossh, tftp, dhcp` plugins
  - PwdFile: To save encrypted passwords in the main config file we need a master key. This entry points to where to read key from and save key to.
  - DevicePwdIsRsa: Enable RSA authentication towards devices
  - DeviceUsr: User YAPT will initiate a device connection with
  - DevicePwd: If YAPT connect by username / password combination this option entry represents the encrypted password
  - ConnectionProbeTimeout: Try to initiate connection to device and retry for n sec    
  - LogFileDirectory: Tells YAPT where to store it's log files
  - StartWebUi: Start web interface listening on port <WebUiPort>
  - WebUiAddress: Webserver IP Address (Used for WebSocket Client)
  - WebUiPort: Webserver Listener Port
  - WebUiIndex: UI index file to load
  - WebUiNat: Enable YAPT WebUI being behind NAT or Proxy 
  - WebUiNatIp: Original IP if behind NAT or Proxy
  - WebUiPlugin: WebUI Plugin (right now only amqp2ws)
  - RestApiPort: YAPT Rest API Listener Port
  - OobaUiPort: YAPT OOBA WebUI interface port
  - WorkerThreads: Amount of task queue worker threads to be started
    * If YAPT runs in Standalone / Vagrant installation this is used to scale parallel task processing
    * In a containerized environment we would use load balancing mechanisms provided by the container system  

### Section: SOURCE ###
Enable different sources for:

- Device data
- Device config template
- Group config
- VNF bootstrap config

Global options regardless of which config source plugin is used are:

```yaml
DeviceConfOoba: false                         #Enable OOBA DB check
DeviceConfSrcPlugins: [local]                 #Configuration source plugin order
```

##### Local #####
This is the default module. All configuration information will be kept in local filesystem.

```yaml
 Local:
    DeviceGrpFilesDir: conf/groups/                 #Map device to a provisioning group
    DeviceConfDataDir: conf/devices/data/           #device specific template data config directory
```
  
##### GITlab #####
This will obtain configuration information from a Gitlab system. Current implementation only supports Gitlab system.

- To use this plugin we have to prepare following repositories in Gitlab:
  + `DevCfg: myrepo/yapt_dev_conf`
  + `DevCfgTemplate: my_repo/yapt_dev_conf_template`
  + `DevGrpCfg: my_repo/yapt_dev_grp_conf`
  + `VnfBoostrapTemplate: my_repo/yapt_vnf_boostrap_template`

Filename schema in repository must be:

- Templates `myfilename.j2`
- Device config `myfilename.yml`
- Group config `myfilenmae.yml`

Device template filename will be read from group configuration task global option `DeviceConfTemplateFile`.
Git source plugin will connect to `Address`, `Port` and `Protocol` with credentials `User` and `Password`.

```yaml
  Git:
    Address: 10.86.9.14
    Port: 9080
    Protocol: http
    LoginUrl: /users/sign_in
    User: root
    Password: password
    DevCfg: demo_ops/yapt_dev_conf
    DevCfgTemplate: demo_ops/yapt_dev_conf_template
    DevGrpCfg: demo_ops/yapt_dev_grp_conf
    VnfBoostrapTemplate: demo_ops/yapt_vnf_boostrap_template
```

### Section: BACKEND ###
YAPT ships with following backend types:

- internal
  * Backend type `internal` is pretty fast but has no persistence
- sql
  * Backend type `sql` is relaying on an RDBMS. In current implementation YAPT uses SQLite

```yaml
BACKEND:

  Module: sql                                    #Backend Type (internal / sql)

    Sqlite:
      DbName: yapt.db                                             #SQLite DB Name
      DbPath: lib/backend/db/                                     #Path to db file
      AutoCreateDb: true                                          #If DB not exists create it automatically
```

### Section: SERVICES ###
Services are tied to source plugins. If adding a source plugin to the source plugin sequence in `yapt.yml` file section `YAPT` the according service has to be configured.

Why separation into services and source plugins? 
Best example for this is the file based service. File based service observes a file for changes. 
The file contents of a tftp log and a dhcp log is different but they are still files being observed by the same file service. 
The source plugin is responsible for "normalizing" the file data read and extracting needed information from it using a pattern.

#### TFTP Service ####
TFTP service observes given file `LogFile` for changes. It matches new file entries to given pattern `Pattern`.


```yaml
Tftp:
    Name: dnsmasq                                           #dnsmasq TFTP Server or hpa TFTP Server
    LogFile: logs/testlogs/tftpd.log                        #Path to the log file being observed (TFTP/DHCP/etc)
    #dnsmasq TFTP Pattern (Ubuntu/Centos)
    Pattern: .*?\sdnsmasq-tftp\[\d.*\]:\ssent\s/var/lib/tftpboot/init.conf\sto\s((?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3}))
```

#### DHCP Service ####
DHCP service observes given file `LogFile` for changes. DHCP service source plugin normalizes and extract needed data.


```yaml
Dhcp:
    Name: isc                                               #dnsmasq DHCP Server or ISC DHCP Server
    LogFile: logs/testlogs/dhcpd.leases                     #Path to the log file being processed
```


#### OSSH Service ####
OSSH "outbound-ssh" is waiting for incoming device initiated SSH session. Listening on `ServiceBindAddress` and `ServiceListenPort`.
A shared secret `SharedSecret` is used to authenticate the device. To allow port forwarding for later use with in-band certificate roll out
device outbound ssh service has to be reconfigured. The ossh source plugin normalizes and extracts the received data.

```yaml
Ossh:
    ServiceBindAddress: 172.16.146.1                        #SSH Server bind address
    ServiceListenPort: 7804                                 #SSH Server listen port
                                                            #DMI Shared Secret
    SharedSecret: gAAAAABZVk8RuO9DYNhx92zfV5yypeMzFMFIkeY2T8GHWeBYs-BqAH7_oaGI7ktDdc9pQkxN9jlQSTtfbluMj0FxT5xlAKbLYA==
    LocalConfigFile: conf/services/ossh/ossh.conf           #Contains mandatory options for device ssh deamon
    RemoteConfigFile: /mfs/var/etc/sshd_config_obssh.yapt   #SSH config file on device. For outbound-ssh should be "/mfs/var/etc/sshd_config_obssh.yapt"
    SigHubCmd: kill -HUP `cat /var/run/inetd.pid`           #Sig HUP inetd to re-read it's configuration
```

#### PHS Service ####
PHS (Phone Home Service / Server) is waiting for incoming http/https sessions. Listening on `ServiceBindAddress` and `ServiceListenPort`.
A bootstrapping configuration is provided in `InitConfPath` directory. Device type has to be determined by this services before sending bootstrap configuration.
This for `device_type` has to be defined in specific device data file in `conf/device/data` directory. PHS can listen on http or https by enable / disable `EnableSSL` option.
Authentication is done by checking received device serial number. Current implementation of an authentication database is a flat file provided by `DeviceAuthFile`.


```yaml
Phs:
    Containerized: false                                    #Is PHS running in container env
    ServiceBindAddress: 172.16.146.1                        #HTTP Server bind address
    ServiceListenPort: 8082                                 #HTTP Server listen port
    InitConfPath: conf/services/phs/                        #Inital bootstrap config file directory
    EnableSSL: false                                        #HTTP or HTTPS used by PHC connection
    SSLCertificate: conf/yapt/ssl/cert.pem                  #SSL Certificate
    SSLPrivateKey: conf/yapt/ssl/privkey.pem                #SSL Private Key
    DeviceAuthFile: conf/services/phs/dev_auth              #device authentication by serial number
```

### Section: JUNOSSPACE ###
Supported Junos Space Platform currently:

- Management platform 15.1R3
- Security Director: 15.1R2
- Management platform 16.1
- Security Director: 16.2 (Only partial support e.g. no firewall rule creation)

Junos Space Rest API connector can be enabled by setting `Enabled` to True or disbaled by setting `Enabled` to False.
Space version has to be set by `Version` to either `space151` or `space161`. 
Space Rest API connector connects to IP `Ip` with user `User` and encrypted password `Password` which has been set by using the password utility. 
YAPT support Junos Space device on-boarding by `discovering` the device or by outbound-ssh initiated device connection using device "configlets".
The discovery task plugin docs have more information about the on-boarding methods. 
The files in `TemplateDir` are being used by the Space Rest API connector to make the right calls since Junos Rest API cahnges from version to version. 
This parameter has to point to the right Junos Space version being used.


```yaml
JUNOSSPACE:
  Enabled: true                                     #Enable / disable Junos Space Connector (True / False)
  Version: space151                                 #Junos Space Version (space151 / space161)
  Ip: 10.200.200.101                                #Junos Space IP address
  User: rest                                        #Junos Space REST API user
                                                    #Junos Space REST API user password
  Password: gAAAAABaIDFdOx8OcSkANaSnHYzOWLaqMIbYLWNR-eTxjYKNC7vOA3stkjlnA7L9hVMYPniwnakW2po197sHZsE3IUTT4ZYEBA==
  TemplateDir: conf/space/templates/151/            #Junos Space REST API Templates (must be right Junos Space version)
  RestTimeout: 3                                    #Junos Space Wait n sec for next rest call
```

### Section: DEVICEDRIVER ###
YAPT has support for two device drivers:

- PyEZ
  * Rich feature set for Junos based devices
  * Tied to Junos based devices
  * All current available provisioning tasks supported
- NAPALM
  * Vendor agnostic
  * Not all current available provisioning tasks supported
  * Mainly used for configuration provisioning

Activate the driver by setting `Driver` to `pyez` or to `napa`. If Napalm is activated as a driver we have to set the module type `Module` to any of the supported Napalm drivers.

```yaml
Driver: pyez                      #pyez / napa (napalm)
  Napalm:                           #Napalm specific options
    Module: junos                   #junos/ios/etc
    Port: 22                        #device port connecting to
```

### Section: AMQP ###
To connect YAPT to the AMQP bus we need to provide `Host`, `Port`, `User` and `Password` values. Password, if YAPT runs in standalone installation mode, will be provided with the password util.


```yaml
AMQP:
  Host: 127.0.0.1
  Port: 5672
  Type: direct
  Exchange: yapt
  User: yapt
  Password: gAAAAABZXKh1cacgc1qPE7Bc2JPcI_G0_2QaGEyr0Yu_6kIoKuVngbRBWcCuzAMrU3hKF0eSDG4lif6WpJdv0upwfWbS5eU70w==
```

### Section: EMITTER ###
YAPT has the capability to emit information to different receivers. Currently YAPT ships with following emitter plugins:

- Local
  + This is the default emitter and emits information to log files
- Ticket
  + The ticket emitter plugin is used when ticket provisioning plugin is enabled
  
To activate / deactivate emitter plugin remove or add them to `Plugins` sequence in `EMITTER` section in main YAPT config file `yapt.yml`.


```yaml
EMITTER:
  Plugins: [local, ticket]
  MainLogFile: logs/info.log
```

### Example Main Config ###

```yaml

---
########################################################################################################################
# YAPT Global Section
########################################################################################################################
YAPT:
  SourcePlugins: [phs, ossh, tftp]                #Source plugin list
  PwdFile: conf/yapt/masterkey.yml                #Stores masterkey
  DevicePwdIsRsa: false                           #use ssh rsa authentication
  DeviceUsr: root                                 #initial device provisioning user
                                                  #initial device provisioning user password
  DevicePwd: gAAAAABaOtwzqu79QGrPMPK1d31hNJ4DMrMruecorE5TTBo00dzanBMK6Ld4Lvtd37ksgP7SPbkqn8ZDmzlnKUWm2WA-yz2UkQ==
  Backend: sql                                    #Backend Type (internal / sql)
  ConnectionProbeTimeout: 90                      #initial connection probe timeout
  LogFileDirectory: logs                          #directory to keep the logs
  StartWebUi: true                                #start web interface listening on port <WebUiPort>
  WebUiAddress: 172.16.146.1                      #Webserver IP Address (Used for WebSocket Client)
  WebUiPort: 8080                                 #Webserver Listener Port
  WebUiIndex: index.html                          #UI index file to load
  WebUiNat: false                                 #Enable YAPT WebUI being behind NAT
  WebUiNatIp: 10.86.9.14                          #NAT IP
  WebUiPlugin: amqp2ws                            #WebUI Plugin (right now only amqp2ws)
  RestApiPort: 9090                               #YAPT Rest Api Listener Port
  OobaUiPort: 9091                                #YAPT Internal OOBA web interface port
  WorkerThreads: 2                                #Amount of task queue worker threads to be started

########################################################################################################################
#Config Source Section
########################################################################################################################
SOURCE:
  DeviceConfOoba: false                         #Enable OOBA DB check
  DeviceConfSrcPlugins: [local]                 #Configuration source plugin order

  File:
    DeviceGrpFilesDir: conf/groups/                 #Map device to a provisioning group
    DeviceConfDataDir: conf/devices/data/           #device specific template data config directory

  Git:
    Address: 10.86.9.14
    Port: 9080
    Protocol: http
    LoginUrl: /users/sign_in
    User: root
    Password: password
    DevCfg: demo_ops/yapt_dev_conf
    DevCfgTemplate: demo_ops/yapt_dev_conf_template
    DevGrpCfg: demo_ops/yapt_dev_grp_conf
    VnfBoostrapTemplate: demo_ops/yapt_vnf_boostrap_template


########################################################################################################################
#Backend Section (Configure Backend settings)
########################################################################################################################
BACKEND:

  Sqlite:
    DbName: yapt.db                                             #SQLite DB Name
    DbPath: lib/backend/db/                                     #Path to db file
    AutoCreateDb: true                                          #If DB not exists create it automatically

########################################################################################################################
#Source Plugins Section
########################################################################################################################
SERVICES:

  Tftp:
    Name: dnsmasq                                           #dnsmasq TFTP Server or hpa TFTP Server
    LogFile: logs/testlogs/tftpd.log                        #Path to the log file being process (TFTP/DHCP/etc)
    #dnsmasq TFTP Pattern (Ubuntu/Centos)
    Pattern: .*?\sdnsmasq-tftp\[\d.*\]:\ssent\s/var/lib/tftpboot/init.conf\sto\s((?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3}))
    #Pattern: '.*?\sdnsmasq-tftp\[\d.*\]:\sTFTP\ssent\s/var/lib/tftpboot/init.conf\sto\s((?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3}))'
    #HPA TFTP Pattern
    #Pattern: '(\d+/\d+/\d+@\d+:\d+:\d+).*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$)'

  Dhcp:
    Name: isc                                               #dnsmasq DHCP Server or ISC DHCP Server
    LogFile: logs/testlogs/dhcpd.leases                     #Path to the log file being processed

  Ossh:
    ServiceBindAddress: 172.16.146.1                        #SSH Server bind address
    ServiceListenPort: 7804                                 #SSH Server listen port
                                                            #DMI Shared Secret
    SharedSecret: gAAAAABZVk8RuO9DYNhx92zfV5yypeMzFMFIkeY2T8GHWeBYs-BqAH7_oaGI7ktDdc9pQkxN9jlQSTtfbluMj0FxT5xlAKbLYA==
    LocalConfigFile: conf/services/ossh/ossh.conf           #Contains mandatory options for device ssh deamon
    RemoteConfigFile: /mfs/var/etc/sshd_config_obssh.yapt   #SSH config file on device. For outbound-ssh should be "/mfs/var/etc/sshd_config_obssh.yapt"
    SigHubCmd: kill -HUP `cat /var/run/inetd.pid`           #Sig HUP inetd to re-read it's configuration

  Phs:
    Containerized: false                                    #Is PHS running in container env
    ServiceBindAddress: 172.16.146.1                        #HTTP Server bind address
    ServiceListenPort: 8082                                 #HTTP Server listen port
    InitConfPath: conf/services/phs/                        #Inital bootstrap config file
    EnableSSL: false                                        #HTTP or HTTPS used by PHC connection
    SSLCertificate: conf/yapt/ssl/cert.pem                  #SSL Certificate
    SSLPrivateKey: conf/yapt/ssl/privkey.pem                #SSL Private Key
    DeviceAuthFile: conf/services/phs/dev_auth              #device authentication by serial number

########################################################################################################################
#Junos Space Section
########################################################################################################################
JUNOSSPACE:
  Enabled: true                                     #Enable / disable Junos Space Connector (True / False)
  Version: space151                                 #Junos Space Version (space151 / space161)
  Ip: 10.200.200.101                                #Junos Space IP address
  User: rest                                        #Junos Space REST API user
                                                    #Junos Space REST API user password
  Password: gAAAAABaIDFdOx8OcSkANaSnHYzOWLaqMIbYLWNR-eTxjYKNC7vOA3stkjlnA7L9hVMYPniwnakW2po197sHZsE3IUTT4ZYEBA==
  TemplateDir: conf/space/templates/151/            #Junos Space REST API Templates (must be right Junos Space version)
  RestTimeout: 3                                    #Junos Space Wait n sec for next rest call

########################################################################################################################
#Device Driver Section
########################################################################################################################
DEVICEDRIVER:
  Driver: pyez                      #pyez / napa (napalm)
  Napalm:                           #Napalm specific options
    Module: junos                   #junos/ios/etc
    Port: 22                        #device port connecting to

########################################################################################################################
#AMQP Related Stuff
########################################################################################################################
AMQP:
  Host: 127.0.0.1
  Port: 5672
  Type: direct
  Exchange: yapt
  User: yapt
  Password: gAAAAABZXKh1cacgc1qPE7Bc2JPcI_G0_2QaGEyr0Yu_6kIoKuVngbRBWcCuzAMrU3hKF0eSDG4lif6WpJdv0upwfWbS5eU70w==

########################################################################################################################
#Logging/Output Related Stuff
########################################################################################################################
EMITTER:
  Plugins: [local, ticket]
  MainLogFile: logs/info.log
```

## Group Config ##

YAPT supports building groups to apply specific tasks to devices.  Add new / edit group files to __conf/groups__. 
Devices will be assigned to a group by setting group name in device data file in __conf/devices/data__ directory.
Group definition has to be set to group file name without file suffix: `device_group`: __srx__.

Here is an example for SRX devices:


```yaml

---
#**********************************************************************************************************************
#GROUP: SRX
#***********************************************************************************************************************

########################################################################################################################
#Tasks Section (turn on/off provisioning tasks / configure specific task settings)
########################################################################################################################
TASKS:
  #Enable tasks and set processing order within sequence
  #Sequence: Init, Filecp, Software, Ipam, Configuration, Cert, Discovery, Policy, Assign, Rule, Publish, Cleanup
  Sequence: [Init, Filecp, Software, Configuration, Cleanup]

  Provision:

    Init:
      Dependencies: [Configuration, Software]

    Assign:
      AssignTemplate: conf/space/151/tempaltes/assignDevice.j2

    Configuration:
      Dependencies: []
      DeviceConfTemplateDir: conf/devices/template/   #device specific template config directory
      DeviceConfTemplateFile: srx_no_ipam_no_ossh.j2  #device config template name
      ConfigFileHistory: history/                     #path to dir where commited device config being saved
      Merge: True                                     #Merge Configuration
      Overwrite: False                                #Replace Configuration

      Internal:
        CommitTimeout: 120                            #Set Commit Timeout to x sec
        ConfirmedTimeout: 1                           #Set Commit confirmed timeout to x min

      Ansibleapi:
        PlaybookPath: conf/ansible/playbooks/         #Set path to playbook
        Playbook: yapt_playbook.yml                   #Set Playbook file name. Playbooks stored in conf/ansible/playbook

    Cert:
      PortForwarding: false                                         #Enable Port Forwarding for cert retrieval
      LocalFwdPort: 5554                                            #Forwarding Port on device
      RemoteFwdHost: 10.15.115.2                                    #Remote host to forward to
      RemoteFwdHostPort: 8080                                       #Port on remote host to forward to
      EnrollmentUrl: ejbca/publicweb/apply/scep/advpn/pkiclient.exe #
      RevocationUrl: ejbca/publicweb/status/ocsp                    #

    Discovery:
      Mode: Discovery                                 #Set discovery mode to either Discovery or Configlet
      UsePing: false                                  #If Mode 'Discovery' use ping
      UseSnmp: true                                   #If Mode 'Discovery' use snmp
      ConnectionConfigletDir: conf/space/configlet/   #modeled device configlet file path

    Filecp:
      Files: [cleanup.slax]                           #File(s) to be copied to device (e.g. SLAX)
      FileLocalDir: scripts/                          #source directory where to find files (defaults to script dir)
      FileRemoteDir: /var/db/scripts/op               #Event/Commit/OP Script or any other directory path on device

    Ipam:
      Module: nipap
      Address: 10.15.115.6
      Port: '1337'
      Prefixes: [10.200.0.0/24, 10.13.113.0/24]
      User: nipap
      Password: nipap

    Policy:
      PolicyTemplate: conf/space/templates/151/fwpolicy.j2
      LookupType: DEVICE

    Rule:
      RuleTemplate: conf/space/templates/151/fwdefaultrule.j2
      RuleTemplateVars: conf/space/templates/151/fwdefaultrule.yml

    Software:
      ImageDir: images/                               #device software images directory
      RemoteDir: /var/tmp/                            #destination directory
      RebootProbeCounter: 30                          #How many times probe should be send while dev rebooting
      RebootProbeTimeout: 30                          #wait n sec starting probing after device is rebooted
      RetryProbeCounter: 5                            #How many times probe should be send while going into reboot
      PkgAddDevTimeout: 1800                          #Timeout for pkgadd function (OSSH)

      TargetVersion:
        FIREFLY-PERIMETER: 12.1X47-D40.1
        VSRX: 15.1X49-D100.6
        SRX100: 12.3X48-D40
        SRX110: 12.3X48-D40
        SRX210: 12.3X48-D40
        SRX220: 12.3X48-D40
        SRX300: 15.1X49-D70
        SRX320: 15.1X49-D70
        SRX340: 15.1X49-D70
        SRX345: 15.1X49-D70

    Ticket:
      Module: rt                                                  #Module currently only request_tracker ticketing system
      Mode: detail                                                #Mode could be "summary" to give a summarization at the end or "detail" to get update after every task
      Address: 10.86.9.14                                         #Ticket System IP address
      Port: 8000                                                  #Ticket System Port
      Protocol: https                                             #HTTP / HTTPS
      User: juniper                                               #Ticket system user
      Password: juniper123                                        #Ticket system passsword
      Eauth: pam                                                  #EDI authentication module
      Functions: [request_tracker.create_ticket, request_tracker.update_ticket]   #call edi runner functions
      NextEvent: None                                             #
      TemplateDir: lib/emitter/templates/                             #Template directory
      TicketCreateTemplate: ticket_create_detail_mode.j2          #Template file used for tickte creation
      TicketUpdateTemplate: ticket_update_detail_mode.j2          #Template file used for ticker update

########################################################################################################################
#Verification Task Section
########################################################################################################################
  Verification:

    Ping:
      Destination: 10.12.111.1
      Count: '10'

    Vpn:
      SaRemoteAddress: 10.11.111.115

    Jsnap:
      Tests: [test_is_equal.yml]
```


## Device Config ##
Device config data will be kept in YAML formatted source. This data is later on being used to generate the device specific configuration.
In group file which the device is assigned to defined template will be used to render final configuration file. YAPT uses Jinja2 template engine
when `Configruation` plugin `internal` is used.

```yaml
DeviceConfTemplateDir: conf/devices/template/   #device specific template config directory
DeviceConfTemplateFile: srx_no_ipam_no_ossh.j2  #device config template name
```

Depending on the provisioning task plugin there are more options to set when it comes to provisioning device configuration.
Some attributes are mandatory and the keyword has to be present in device config even if it's not used. If not used just left the value empty.
Format of device's data file consists of two main sections:

### Yapt section ###
- `device_type` 
  + Device type is mainly used for PHS. Since XML bootstrapping data looks different between a SRX and a NFX YAPT needs to know which device it is talking to  
- `device_group`
  + Assign device to a group to run specific tasks
- `service_chain`
  + Build a service chain to instruct YAPT to wait for device connecting by another service in a second step after initial bootstrapping 
  + Main use case is PHS --> OSSH. Device first will connect to YAPT using PHS then after boostrap config being applied device initiates OSSH connection
  + `service_chain` would then look like: `service_chain: [ossh]`
- `bootstrap_template_dir` and `bootstrap_template_file` is used for VNF provisioning only and points to the VNF specific configuration

```yaml
yapt:
  device_type: srx
  device_group: srx
  service_chain: []
  bootstrap_template_dir: conf/vnf/template
  bootstrap_template_file: vsrx_ztp_bootstrap.j2
```

|Attribute                  |Description            |Mandatory  |
|---                        |---                    |---        |
|device_type                |Set device type        |yes        |
|device_group               |Set device group       |yes        |
|service_chain              |Build service chain    |yes        |
|bootstrap_template_dir     |VNF template dir       |yes        |
|bootstrap_template_file    |VNF template file      |yes        |

### Device section ###
Most of the values defined in the `device` section referring to the template to be used. 
There is currently one exception which is the `Cert` provisioning plugin. If `Cert` plugin is being used we have mandatory statements in this file.
Please have a look at the task plugin section to get more information about the `Cert` provisioning plugin and the mandatory statements. 

```yaml
device:
  hostname: vsrx_ztp01
  encrypted_password: $5$Wbt5G9uy$IW32MqVW.3.sxbrz0jzs4X/JrTAbNk1E41N9.lMO0j5
  ossh_secret: $9$m5zntu1ylM/ClM8XbwmfT
  timezone: Europe/Berlin
  domain_name: mycompany.local
  ntp_server: 10.21.28.2
  community: public
  interfaces:
  - name: fxp0
    description: MGMT
    family: inet
    address: dhcp
  - name: ge-0/0/0
    description: MGMT
    family: inet
    address: dhcp
  - name: ge-0/0/1
    description: untrust
    family: inet
    address: dhcp
  - name: ge-0/0/2
    description: trust
    family: inet
    address: 10.12.112.254
    mask: 24
  tunnel_int:
    name: st0
    description: VPN
    unit: 0
    family: inet
    address: ipam
    mask: 24
  cert:
    ca_profile: ejbca
    ca_identity: advpn
    subject: CN=vsrx_ztp01,OU=IT,O=MyCompany,L=Berlin,DC=mycompany.local,C=DE
    domain_name: vsrx_ztp01.mycompany.local
    enrollment_url: ejbca/publicweb/apply/scep/advpn/pkiclient.exe
    oscp_url: ejbca/publicweb/status/ocsp
    challenge_password: juniper123
    revocation_url: ejbca/publicweb/status/ocsp
```

Example of a device template file:

```text
{{ heading }}
system {
    host-name {{ device.hostname }};
    time-zone {{ device.timezone }};
    domain-name {{ device.domain_name }};
    root-authentication {
        encrypted-password "{{ device.encrypted_password }}"; ## SECRET-DATA
    }
    services {
        ssh {
            protocol-version v2;
        }
        netconf {
            ssh;
        }
        outbound-ssh {
            client yapt {
                device-id abc123;
                secret "$9$jckmT69pRhrz3hrev7Nik.Pz3/CtOIE"; ## SECRET-DATA
                services netconf;
                172.16.146.1 port 7804;
            }
        }
    }
    syslog {
        user * {
            any emergency;
        }
        file messages {
            any any;
            authorization info;
        }
        file interactive-commands {
            interactive-commands any;
        }
    }
    license {
        autoupdate {
            url https://ae1.juniper.net/junos/key_retrieval;
        }
    }
    ntp {
        server {{ device.ntp_server }};
    }
    scripts {
        op {
            file cleanup.slax
        }
    }
}
interfaces {
    {% for interface in device.interfaces %}
    {% if interface.address == "dhcp" %}
    {{ interface.name }} {
        description "{{ interface.description }}";
        unit 0 {
            family {{ interface.family }} {
                dhcp-client;
            }
        }
    }
    {% elif interface.name == "ge-0/0/0" %}
    replace: {{ interface.name }} {
        description "{{ interface.description }}";
        unit 0 {
            family {{ interface.family }} {
                address {{ ipam['IP1'] }}/{{ interface.mask }};
            }
        }
    }
    {% else %}
    {{ interface.name }} {
        description "{{ interface.description }}";
        unit 0 {
            family {{ interface.family }} {
                address {{ interface.address }}/{{ interface.mask }};
            }
        }
    }
    {% endif %}
    {% endfor %}
    {{ device.tunnel_int.name }} {
        unit {{ device.tunnel_int.unit }} {
            family {{ device.tunnel_int.family }} {
                address {{ ipam['IP0'] }}/{{ device.tunnel_int.mask }};
            }
        }
    }
}
snmp {
    community {{ device.community }} {
        authorization read-only;
    }
}
routing-options {
    router-id {{ ipam['IP0'] }};
}
protocols {
    ospf {
        export AutoVPN;
        area 0.0.0.0 {
            interface {{ device.tunnel_int.name }}.{{ device.tunnel_int.unit }} {
                interface-type p2p;
            }
        }
    }
}
policy-options {
    policy-statement AutoVPN {
        term direct_term {
            from {
                protocol direct;
                {% for interface in device.interfaces %}
                {% if interface.description == "trust" %}
                interface {{ interface.name }}.0;
                {% endif %}
                {% endfor %}
            }
            then accept;
        }
        term ospf_term {
            from protocol ospf;
            then accept;
        }
    }
}
security {
    pki {
        ca-profile {{ device.cert.ca_profile }} {
            ca-identity {{ device.cert.ca_identity }};
            enrollment {
                url {{ device.cert.enrollment_url }};
            }
            revocation-check {
                disable;
            }
        }
        auto-re-enrollment {
            certificate-id {{ device.hostname }} {
                ca-profile-name {{ device.cert.ca_profile }};
                challenge-password "{{ device.cert.challenge_password }}"; ## SECRET-DATA
                re-enroll-trigger-time-percentage 10;
                re-generate-keypair;
                scep-encryption-algorithm {
                    des3;
                }
                scep-digest-algorithm {
                    sha1;
                }
            }
        }
    }
    ike {
        proposal P1 {
            authentication-method rsa-signatures;
            dh-group group14;
            authentication-algorithm sha-256;
            encryption-algorithm aes-256-cbc;
            lifetime-seconds 28800;
        }
        policy AutoVPN {
            mode main;
            proposals P1;
            certificate {
                local-certificate {{ device.hostname }};
            }
        }
        gateway AutoVPNHub {
            ike-policy AutoVPN;
            address 10.13.113.1;
            dead-peer-detection {
                interval 10;
                threshold 1;
            }
            no-nat-traversal;
            local-identity distinguished-name;
            remote-identity distinguished-name;
            {% for interface in device.interfaces %}
            {% if interface.description == "untrust" %}
            external-interface {{ interface.name }}.0;
            {% endif %}
            {% endfor %}
            version v2-only;
        }
    }
    ipsec {
        proposal P2 {
            protocol esp;
            authentication-algorithm hmac-sha1-96;
            encryption-algorithm aes-256-cbc;
            lifetime-seconds 3600;
        }
        policy AutoVPN {
            perfect-forward-secrecy {
                keys group14;
            }
            proposals P2;
        }
        vpn AutoVPN {
            bind-interface {{ device.tunnel_int.name }}.{{ device.tunnel_int.unit }};
            ike {
                gateway AutoVPNHub;
                ipsec-policy AutoVPN;
            }
            establish-tunnels immediately;
        }
    }
    flow {
        tcp-mss {
            ipsec-vpn {
                mss 1350;
            }
        }
    }
    screen {
        ids-option untrust-screen {
            icmp {
                ping-death;
            }
            ip {
                source-route-option;
                tear-drop;
            }
            tcp {
                syn-flood {
                    alarm-threshold 1024;
                    attack-threshold 200;
                    source-threshold 1024;
                    destination-threshold 2048;
                    queue-size 2000;
                    timeout 20;
                }
                land;
            }
        }
    }
    policies {
        from-zone trust to-zone untrust {
            policy default-permit {
                match {
                    source-address any;
                    destination-address any;
                    application any;
                }
                then {
                    permit;
                }
            }
        }
        from-zone untrust to-zone trust {
            policy default-deny {
                match {
                    source-address any;
                    destination-address any;
                    application any;
                }
                then {
                    deny;
                }
            }
        }
        from-zone trust to-zone vpn {
            policy default-permit {
                match {
                    source-address any;
                    destination-address any;
                    application any;
                }
                then {
                    permit;
                }
            }
        }
        from-zone vpn to-zone trust {
            policy default-permit {
                match {
                    source-address any;
                    destination-address any;
                    application any;
                }
                then {
                    permit;
                }
            }
        }
    }
    zones {
        security-zone trust {
            tcp-rst;
            interfaces {
            {% for interface in device.interfaces %}
                {% if interface.description == "trust" %}
                {{ interface.name }}.0 {
                    host-inbound-traffic {
                        system-services {
                            http;
                            https;
                            ssh;
                            dhcp;
                            netconf;
                            ping;
                            traceroute;
                        }
                    }
                }
                {% endif %}
            {% endfor %}
            }
        }
        security-zone untrust {
            screen untrust-screen;
            interfaces {
            {% for interface in device.interfaces %}
                {% if interface.description == "untrust" %}
                {{ interface.name }}.0 {
                    host-inbound-traffic {
                        system-services {
                            https;
                            ssh;
                            dhcp;
                            netconf;
                            ike;
                            ping;
                            traceroute;
                            snmp;
                        }
                    }
                }
                {% endif %}
            {% endfor %}
            }
        }
        security-zone vpn {
            interfaces {
                {{ device.tunnel_int.name }}.{{ device.tunnel_int.unit }} {
                    host-inbound-traffic {
                        system-services {
                            ping;
                            traceroute;
                        }
                        protocols {
                            ospf;
                        }
                    }
                }
            }
        }
    }
}
```

## Task Config ##
YAPT provides two task categories:

- Provisioning Tasks
- Verification Tasks

Tasks will be activated in device group files. To activate a task add it to the task sequence list `Sequence: [Init, Filecp, Software, Configuration, Cleanup]`.
To deactivate remove it from the task sequence list. Tasks in this list will be processed in order of occurrence. First letter of task name has always to be a capital letter.
Ordering of the tasks can be easily changed. Only exception are the task `Init` which should always be in first place and task `Cleanup` which should always be at the end of the sequence.
 
```yaml
TASKS:
  #Enable tasks and set processing order within sequence
  Sequence: [Init, Filecp, Software, Configuration, Cleanup]
```

Tasks are all plugin based and stored in `lib/tasks`. Depending on the configured driver in `DEVICEDRIVER` section YAPT loads activated tasks in task `Sequence`.
Tasks have different states:

- Init state
  + Task loads all dependencies and data and changes to `init` state
- Done state
  + Task successfully finished it's job and changes to `done` state
- Failed state
  + An error occured and task state changes to `failed` state
- Progress state
  + Task is working / running doing it's job and changes to `progress` state
- Reboot state
  + Task is waiting for a device reboot and changes to `reboot` state
- Waiting state
  + Task is in waiting state after task creation process

Tasks could have dependencies with other tasks. Therefor current task has to load / execute other jobs before actual tasks work can be done.
Dependencies can be defined for every task in the task plugin section in group file with `Dependencies` statement. 

### Provisioning Tasks ###

#### Assign ####
This task is used within Junos Space on boarding process. It assigns firewall policy object to device object.


```yaml
Assign:
      AssignTemplate: conf/space/151/tempaltes/assignDevice.j2
```


#### Configuration ####
Configuration task has global options regardless of which implementation is used. Global options are:

- `Dependnecies`: Configuration task plugins often have dependencies like for `Ipam` or `Cert` task data to be pulled
- `DeviceConfTemplateDir`: Defines directory where to look for device template files. Will be used when config source is set to `local`
- `DeviceConfTemplateFile`: Defines the template file to be loaded for configuration generation
- `ConfigFileHistory`: Saves rendered configuration file in configured directory
- `Merge`: Merge config (True / False)
- `Overwrite`: Overwrite config (True / False)
```yaml


Configuration:
      Dependencies: []
      DeviceConfTemplateDir: conf/devices/template/   #device specific template config directory
      DeviceConfTemplateFile: srx_no_ipam_no_ossh.j2  #device config template name
      ConfigFileHistory: history/                     #path to dir where commited device config being saved
      Merge: True                                     #Merge Configuration
      Overwrite: False                                #Replace Configuration
```

##### Ansibleapi #####
If not already done to use Ansible provisioning task plugin you will need to install Ansible Junos role with:

```bash
ansible-galaxy install Juniper.junos
```

To use provisioning task `ansibleapi` configure the playbook path with `PlaybookPath` and the playbook file with `Playbook`. 

Constrains with task plugin `ansibleapi`:
- Ansibleapi task can't be used together with in-band certificate roll out
- Ansibleapi task won't work with new device sitting behind NAT device
- Ansibleapi task always initiate connection to device


```yaml
Ansibleapi:
        PlaybookPath: conf/ansible/playbooks/         #Set path to playbook
        Playbook: yapt_playbook.yml                   #Set Playbook file name. Playbooks stored in conf/ansible/playbook
```

##### Internal #####
With `Internal` configuration provisioning plugin we use device data and template source to generate device specific configuration.
Current available options are 

- `CommitTimeout`: wait n sec for commit response
- `ConfirmedTimeout`: wait n sec firing commit confirmed   

```yaml
      Internal:
        CommitTimeout: 120                            #Set Commit Timeout to x sec
        ConfirmedTimeout: 1                           #Set Commit confirmed timeout to x min
```

### Init ###
Depending on which device driver choosen `Init` task prepares connection object to support specific functionality. In case of `Init` task and PyEz as device driver we support
`Configuration` and `Software` provisioning. 

```yaml
Init:
      Dependencies: [Configuration, Software]
```

#### Cert ####
Cert Task is used for in-band certificate roll out. We can use existing SSH session between YAPT and device to install the certificates.
This could be done by using `PortForwarding`. When enabled we have to set local forwarding port `LocalFwdPort` on device.
Setting the remote host with `RemoteFwdHost` we want to forward to and the destination port with `RemoteFwdHostPort`.
`EnrollmentUrl` and `RevocationUrl` are pointing to specific CA systems SCEP / OCSP urls.
Cert plugin has been tested with EJBCA CA software. If `Cert` plugin is used we have set below mandatory configuration options in device config file.


```yaml
Cert:
      PortForwarding: false                                         #Enable Port Forwarding for cert retrieval
      LocalFwdPort: 5554                                            #Forwarding Port on device
      RemoteFwdHost: 10.15.115.2                                    #Remote host to forward to
      RemoteFwdHostPort: 8080                                       #Port on remote host to forward to
      EnrollmentUrl: ejbca/publicweb/apply/scep/advpn/pkiclient.exe #
      RevocationUrl: ejbca/publicweb/status/ocsp                    #
```

#### Discovery ####
The discovery plugin is used to on-board device with Junos Space. There are two modes (`Mode`)available to on-board device:

- Discovery
  + Junos Space initiated device discovery process being triggered by YAPT
- Configlet
  + Using outbound-ssh (configlet) approach. Connection will be initiated by device
    * Create a device instance (Modeled device) in Junos Space
      + Instance name must be the __DEVICE_TYPE__ name
    * Create `connectionConfigletVars.yml` directory `ConnectionConfigletDir/__DEVICE_TYPE__` 
    * Example `conf/space/configlet/SRX300/connectionConfigletVars.yml`
    * Copy `connectionConfiglet.j2` file from doc boilerplate directory

YAPT will automatically add additional instances to existing one. 

```yaml
Discovery:
      Mode: Discovery                                 #Set discovery mode to either Discovery or Configlet
      UsePing: false                                  #If Mode 'Discovery' use ping
      UseSnmp: true                                   #If Mode 'Discovery' use snmp
      ConnectionConfigletDir: conf/space/configlet/   #modeled device configlet file path
```

#### Filecp ####
Copies files in `Files` from `FileLocalDir` to specified directory `FileRemoteDir`. 

```yaml
Filecp:
      Files: [cleanup.slax]                           #File(s) to be copied to device (e.g. SLAX)
      FileLocalDir: scripts/                          #source directory where to find files (defaults to script dir)
      FileRemoteDir: /var/db/scripts/op               #Event/Commit/OP Script or any other directory path on device
```

Top copy multiple files add additional entires to `Files` like `[file1.slax, file2.txt, file3.sh, cleanup.slax]`
`cleanup.salx` should be kept in the list.

#### Ipam ####
Current available Ipam plugin is `nipap`. Via `Module` could be other modules defined. 
Ipam plugin connects to `Address` and `Port`. Plugin uses credentails `User` and `Password` to authenticate to Ipam system.
Defining the list of prefixes we want IPs from with `Prefixes`. Prefixes later on can be accessed in device template file with `ipam['IPX']` where `X` is the prefix in our list.

```text
{{ device.tunnel_int.name }} {
        unit {{ device.tunnel_int.unit }} {
            family {{ device.tunnel_int.family }} {
                address {{ ipam['IP0'] }}/{{ device.tunnel_int.mask }};
            }
        }
    }
``` 


```yaml
Ipam:
      Module: nipap
      Address: 10.15.115.6
      Port: '1337'
      Prefixes: [10.200.0.0/24, 10.13.113.0/24]
      User: nipap
      Password: nipap
```

#### Policy ####
Policy plugin is used to create a security policy object in Junos Space.

```yaml
Policy:
      PolicyTemplate: conf/space/templates/151/fwpolicy.j2
      LookupType: DEVICE
```

#### Rule ####
Rule plugin is used to add a security rule to security policy in Junos Space.

```yaml
Rule:
      RuleTemplate: conf/space/templates/151/fwdefaultrule.j2
      RuleTemplateVars: conf/space/templates/151/fwdefaultrule.yml
```

#### Software ####
Software plugin installs image kept in directory `ImageDir` onto device. 
We define the remote directory where the image should be copied to during update process by setting `RemoteDir`.
`RebootProbeCounter` probes n times to check if device is back from reboot. `RebootProbeTimeout` checks every n sec if device got into reboot state.
`RetryProbeCounter` checks n times if device got into reboot state. `PkgAddDevTimeout` is specific value for outbound-ssh based software update and defines
the time to wait for rpc response during software update. Define a mapping with `TargetVersion` between __DEVICE_TYPE__ and the target software version being installed.


```yaml
Software:
      ImageDir: images/                               #device software images directory
      RemoteDir: /var/tmp/                            #destination directory
      RebootProbeCounter: 30                          #How many times probe should be send while dev rebooting
      RebootProbeTimeout: 30                          #wait n sec starting probing after device is rebooted
      RetryProbeCounter: 5                            #How many times probe should be send while going into reboot
      PkgAddDevTimeout: 1800                          #Timeout for pkgadd function (OSSH)

      TargetVersion:
        FIREFLY-PERIMETER: 12.1X47-D40.1
        VSRX: 15.1X49-D100.6
        SRX100: 12.3X48-D40
        SRX110: 12.3X48-D40
        SRX210: 12.3X48-D40
        SRX220: 12.3X48-D40
        SRX300: 15.1X49-D70
        SRX320: 15.1X49-D70
        SRX340: 15.1X49-D70
        SRX345: 15.1X49-D70
```

#### Ticket ####
Current supported ticket system is RT and so parameter `Module` has to be set to `rt`. 

Ticket plugin supports two modes:
- The mode `detail` updates ticket after tasks successfully done 
- The mode `summary` updates ticket after all tasks done

YAPT connects to EDI webhook by `Address`, `Port` and `Protocol` with credentials `User` and `Password`. These are settings
which have to be configured on the EDI system.
The parameter `TemplateDir` points to template directory for rendering ticket contents. If ticket is created the first time we use template `TicketCreateTemplate`.
If ticket is updated we use `TicketUpdateTemplate` template.
Enable ticket plugin by adding it to the task sequence list in group file. 
- If ticket plugin mode is `detail` place it before `Init` task (Yes, that's an exception)
  * Check if emitter plugin `ticket` is in emitter `Plugins` sequence in YAPT main config file section `EMITTER`
- If ticket plugin mode is `summary` place it after `Cleanup` task (Yes, that's an exception too)

```yaml
Ticket:
      Module: rt                                                  #Module currently only request_tracker ticketing system
      Mode: detail                                                #Mode could be "summary" to give a summarization at the end or "detail" to get update after every task
      Address: 10.86.9.14                                         #Ticket System IP address
      Port: 8000                                                  #Ticket System Port
      Protocol: https                                             #HTTP / HTTPS
      User: juniper                                               #Ticket system user
      Password: juniper123                                        #Ticket system passsword
      Eauth: pam                                                  #EDI authentication module
      Functions: [request_tracker.create_ticket, request_tracker.update_ticket]   #call edi runner functions
      NextEvent: None                                             #
      TemplateDir: lib/emitter/templates/                             #Template directory
      TicketCreateTemplate: ticket_create_detail_mode.j2          #Template file used for tickte creation
      TicketUpdateTemplate: ticket_update_detail_mode.j2          #Template file used for ticker update
```


### Verification Tasks ###
TBD


## User and Passwords ##
YAPT ships with password utility, which is used to save encrypted passwords in YAPT configuration files.
With password utility we can generate most of the passwords. Main goal of password util is to encrypt password in YAPT config files. 
Current implementation is not intended to be secure since master key has to be protected on it's own.

This tool can be started by following command:

- cd lib/utils
- PYTHONPATH=__PATH_TO_YAPT_INSTALLATION__ /usr/local/bin/python2.7 ./password.py
- First of all you need to create a master key. If there is already a master key this won't be overwritten and has to be deleted from master key file


```
PYTHONPATH=/root/juniper-yapt-0.0.2/ /usr/local/bin/python2.7 password.py

------------------------------ Password Util ------------------------------
1. Create Master Key
2. Generate Device SSH Password
3. Generate Junos Space REST Api Password
4. Generate OSSH Shared Secret
5. Generate AMQP Password
6. Exit
---------------------------------------------------------------------------
Enter your choice [1-6]:
```

## Device Authentication ##
YAPT supports password and key based device authentication. For password based authentication you use password util to generate the device password. If key based authentication is being used following settings have to be done:

- Change password mode by setting __DevicePwdIsRsa__ to __True__ in __yapt.yml__ global section

```
DevicePwdIsRsa: False                           #use ssh rsa authentication
```

- Generate ssh private / public key
  * cd conf/yapt
  * ssh-keygen -b 2048 -t rsa -f id_rsa -P ""
- Public key id_rsa.pub can later on be used in bootstrap configuration
  * PHS bootstrap config example:

```
<ssh-rsa>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDNRZHZGfeKpivvJxvcLEFbn37+m9HaAAjX5yPdHR/p9YBme+S7P9OcQv3Y5aRLsDjmGI3jqnEDDtw8XxS/Ky2DQ9g/uVb++MWTOu739iJiF6wwOJXUvFLbFzG8TF1i0mrGYyZ/5UtPL1YWrKnRO86mhbQDPie9H8dIoZb1AYBEugm0GwOqA0luRuAgvoAuOr15qYu0zDcwXF3f5ZpRh8TcVgWsPQ/HQK/WaWjOyeUz6a7iC1VtcmXn3LY6RG2iTCSxQz6n1Z/JBEUQfjKG9o9XEZ7Pf3eN8tGbTWXtiQVsfJ1VXTOPm/YUaABIhY5t72K3F7mMwoQmVS2GpG2PwRgr cklewar@cklewar-mbp</ssh-rsa>
```

## Starting / stopping services ##
In standalone or vagrant installation YAPT needs rabbitmq service to be started prior to yapt service. 
This is platform specific and could be done using Linux init scripts under __/etc/init.d__ or on systemd based systems with __systemctl__ or __service__ commands.
YAPT ships with a start / stop script called __yapt.sh__.
* __yapt.sh start__ starts yapt
* __yapt.sh stop__ stops yapt

This doesn't apply do a docker based installation.

## Logging ##

* YAPT writes log information into
    - logs/info.log (informational)
    - logs/error.log (debug)
* A __tail -f info.log | grep YAPT__ will show each provsioning tasks status.

## WebUI ##
WebUI URL is __http://ip:port/yapt/ui__

## OOBA WebUI ##
OOBA WebUI URL is __http://ip:port/ooba__

## Additional Services ##
For devices like EX/QFX we need additional services like DHCP / TFTP server. 
Here some example configurations of those:

### DHCP server (ISC DHCP) ###

```ini
option domain-name "yapt.local";

default-lease-time 600;
max-lease-time 7200;

log-facility local7;

allow booting;
allow bootp;
allow unknown-clients;

subnet 192.168.60.0 netmask 255.255.255.0 {

range 192.168.60.50 192.168.60.254;
option broadcast-address 192.168.1.255;
option routers 192.168.1.1;
next-server 192.168.60.6;
filename "init.conf";

}
```

#### TFTP server (HPA-TFTP) ####

```ini
service tftp
{
	disable	        = no
	socket_type		= dgram
	protocol		= udp
	wait			= yes
	user			= root
	server			= /usr/sbin/in.tftpd
	server_args		= -s /var/lib/tftpboot -t 120 -v
	per_source		= 11
	cps			    = 100 2
	flags			= IPv4
	log_type        = FILE /var/log/tftpd.log
}
```

#### TFTP server (dnsmasq) ####

```ini
# Disable DNS
port=0

# Enable the TFTP server
enable-tftp
tftp-root=/var/lib/tftpboot
tftp-no-blocksize
# Enable Logging
log-facility=/var/log/tftpd.log
```

#### Bootstrap TFTP config file "Centralized Provisioning approach" ####
This example __init.conf__ config file should be copied to TFTP servers directory like specified in dnsmasq configuration above.
The __root__ user is used for YAPT connecting to device for starting the provisioning process. 

Here is an example for an vSRX (FireFly) device:

```xml
system {
    host-name init;
    root-authentication {
        encrypted-password "$1$B3h1HvJj$8wD6QXpmo6h8q.ezlj/FW/"; ## SECRET-DATA
    }
    services {
        ssh;
        netconf {
            ssh;
        }
    }
    syslog {
        user * {
            any emergency;
        }
        file messages {
            any any;
            authorization info;
        }
        file interactive-commands {
            interactive-commands any;
        }
    }
    license {
        autoupdate {
            url https://ae1.juniper.net/junos/key_retrieval;
        }
    }
}
interfaces {
    ge-0/0/0 {
        unit 0 {
            family inet {
                dhcp-client;
            }
        }
    }
}
security {
    zones {
        security-zone untrust {
            interfaces {
                ge-0/0/0.0 {
                    host-inbound-traffic {
                        system-services {
                            traceroute;
                            ping;
                            ssh;
                            netconf;
                            ike;
                            snmp;
                            dhcp;
                        }
                    }
                }
            }
        }
    }
}
```

# YAPT Rest API #


## Add device to trust store ##

```text
http://172.16.146.1:9090/api/authenticate?sn=8809EA3C6C21
```

# Directory structure #
YAPT directory structure

1. __doc__:  YAPT documentation and example configurations, boilerplate
2. __scripts__: put script files in here which should be copied to the device and run for automation purposes
3. __logs__: keeps logs for debugging. e.g. tail -f info.log | grep tool
    * __testlogs__: keeps test log files for tftp and dhcp server
4. __images__: keeps the software images
5. __history__: keeps a history of already uploaded configuration files to a device
6. __conf__: keeps YAPT own config files
    * __ansible__: keeps ansible related files
    * __devices__: keeps device specific configuration / templates
    * __groups__: keeps device group related configuration files
    * __jsnapy__ keeps jsnapy related files
    * __plugins__: keeps source plugin description files
    * __schema__ keeps config validation schema files
    * __services__: keeps service configuration / related files
    * __space__: keeps Junos Space related files
    * __vnf__ keeps vnf bootsraping stuff
    * __yapt__: keeps yapt config file (yapt.yml)   
7. __lib__: YAPT libraries
    * __amqp__: amqp bus
    * __backend__: internal / sql
    * __config__: config source plugins
    * __emitter__: emitter plugins
    * __plugins__: source plugins
    * __services__: services (OSSH / PHS / FILE)
    * __space__: Junos Space connector
    * __tasks__: provisioning tasks / verification tasks
    * __utils__: currently password manager
    * __web__: web related files (REST API / UI)
