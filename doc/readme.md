# Introduction #

YAPT is a tool to demonstrate Juniper automation capabilities on SRX / EX / VMX / NFX platform. Zero Touch Provisioning could be demonstrated for example during customer PoC.

# Use Cases #

## Centralised Provisioning before shipment ##

During the boot sequence the device will get initial configuration parameters and connects to a centralised server that would
build and deliver a location specific configuration. In this particular use case location is determined
by device's serial number. But could also be any other device specific information.

Each provisioning task can be turned “on/off” and the order in which tasks are being processed can be changed to reflect uses cases / requirements..
Once all tasks are done, device can be shipped to final destination.
The ability to provision more than one device at the same time is also possible within the YAPT workflow.

## Decentralized provisioning with Phone Home ##

Device will be shipped to final destination directly.

The provision process consists of several tasks:
* Device calls home using Juniper redirect service pointing to YAPT
* Bootstrap config will be applied using Phone Home
* YAPT receives request and starts provisioning process

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
YAPT can pull config files for devices and groups from different sources. YAPT ships with following config source plugins:

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

Current integration is with RT ticketing system. We could demonstrate updating a ticket with privisoning / verification task information.   
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

- Edit __conf/yapt/yapt.yml__ file under conf/yapt directory to fit your environment settings
  - Parameter __SourcePlugins__: Set the source plugin to the one you want to be used and configure source plugins settings under __Global Section__ in __yapt.yml__
  - Parameter __WebUiAddress__: should be set to interface IP WebUI will be reachable
  - If YAPT server operates behind NAT / Proxy we need to set:

  
  ```
  WebUiNat: False                                 #Enable YAPT WebUI being behind NAT
  WebUiNatIp: 172.30.162.52                       #NAT IP
  ```

- Configure the services which have been enabled under __SourcePlugins__ section

# Configuration #

## Main Config ##

YAPT main config file `conf/yapt/yapt.yml` consists of following sections:
All settings in this file have a global scope.

### Section YAPT ###


  - SourcePlugins: Enable source plugins and their respective service
    + Currently YAPT ships with `phs, ossh, tftp, dhcp` plugins
  - PwdFile: To save encrypted passwords in the main config file we need a master key. This entry points where to read key from and save key to.
  - DevicePwdIsRsa: Enable RSA authentication towards devices
  - DeviceUsr: User YAPT will initiate a device connection with
  - DevicePwd: If YAPT connect by username / password combination this option entry represents the encrypted password
  - Backend: Choose the backend type to use
    * Currently YAPT ships with two backend types
      * Backend type `internal` is pretty fast but has no persistency
      * Backend type `sql` is relaying on an RDBMS. In current implementation YAPT uses SQLite
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

### Section SOURCE ###

- DeviceConfOoba: Enable OOBA mapping checks
- DeviceConfSrcPlugins: Configuration source plugin order

### Section Backend ###
TBD


### Section SERVICES ###
TBD

### Section JUNOSPACE ###
TBD

### Section DEVICEDRIVER ###
TBD

### Section AMQP ###
TBD

### Section EMITTER ###
TBD

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
Devices will be assigned to a group by setting group name in device data file under __conf/devices/data__.
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

```yaml
yapt:
  device_type: srx
  device_group: srx
  service_chain: []
  bootstrap_template_dir: conf/vnf/template
  bootstrap_template_file: vsrx_ztp_bootstrap.j2

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

## Task Config ##
YAPT provides two task categories:

- Provisioning Tasks
- Verification Tasks

Tasks will be activated in device group files. To activate a task add it to the task sequence list `Sequence: [Init, Filecp, Software, Configuration, Cleanup]`.
To deactivate remove it from the task sequence list. Tasks in this list will be processed in order of occurrence. First letter of task name in this sequence list hast to be a capital letter.
Only exception is task plugin `Init` which should always be in first place and task plugin `Cleanup` which should always be at the end of the sequence.
 
### Provisioning Tasks ###

#### Ansibleapi ####

If not already done to use Ansible provisioning task plugin you will need to install Ansible Junos role with:

```bash
ansible-galaxy install Juniper.junos
```

Provisioning task `ansibleapi`

```yaml
Ansibleapi:
        PlaybookPath: conf/ansible/playbooks/         #Set path to playbook
        Playbook: yapt_playbook.yml                   #Set Playbook file name. Playbooks stored in conf/ansible/playbook
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

- Change password mode by setting __DevicePwdIsRsa__ to __True__ in __yapt.conf__ global section

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
This is platform specific which could be done using Linux init scripts under __/etc/init.d__ or on systemd based systems with __systemctl__ or __service__ commands.
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
Default WebUI URL is __http://ip:port/yapt/ui__

## OOBA WebUI ##
OOBA WebUI URL is __http://ip:port/ooba__

## Additional Services ##
If the centralised approach will be used we need additional services like DHCP / TFTP server. 
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
This example __init.conf__ config file should be copied to TFTP servers directory.
The __root__ user is used for YAPT connecting to device for starting the provisioning process.

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


## JunOS Space ##
Supported Junos Space Platform currently:

- Management platform 15.1R3
- Security Director: 15.1R2
- Management platform 16.1
- Security Director: 16.2 (Only partial support e.g. no firewall rule creation)

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
