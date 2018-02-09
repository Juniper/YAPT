# Introduction #

YAPT is a tool to demonstrate Juniper automation capabilities on SRX / EX / VMX / NFX platform. Zero Touch Provisioning could be demonstrated for example during customer PoC.

# Architecture #
YAPT has a modular architecture based on plugins and a bus system.

## Bus ##
YAPT uses AMQP based bus for internal communication between "Processors".

## Processor ##
A processor in YAPT architecure receives / sends messages using underlaying bus. Processor starts for example a provisioning task or sends updates to WebUI. Source plugins are the starting point generating messages.

## Source plugins ##
A source plugin relays on a service. Currently YAPT ships with three services:
  * PHS service
       + Provision process can be triggered using Phone Home client
  * Outbound-ssh service
      + Device initated ssh connection points to YAPT
      + Outbound-ssh plugin can be used for automatic in band certificate roll out
      + It's currently not possible to use outbound-ssh together with the software provisioning task
  * File service
      + DHCP servers log file
      + TFTP servers log file
      + Could be any file we looking for changes

A file based source plugin would use the file service which is listening for file change notifications. It is possible extend YAPT capabilities by adding new source plugins / services.


## Provisioning tasks ##
Provisioning tasks are doing the work when it comes to "provisioning" the device. There are tasks for:

* Software Update
* Configuration deployment
  + Uses template based configuration generation
* IPAM
  + currently supported IPAM is nipap
* File Copy (used for copying files to device)
* Certificate roll out (provision certificates for e.g. ADVPN / AutoVPN)
* Junos Space device discovery
* Junos Space SD security policy creation
* Junos Space SD rule creation
* Junos Space SD assign policy to device
* Junos Space SD push changes to device

It's possible to extend YAPT capabilities by adding new to tasks. Tasks are worked on in a sequential order which can be changed or turned on / off.

## Verification tasks ##
Verification tasks could be used to check for certain state on the device. For example check if IPSec VPN tunnel and OSPF neighbours are up. Currently there are is only one verification task shipping with YAPT. I think this could be done better using JSNAPY.

## Backend ##
YAPT supports different backend types. Standard backend is called "internal". This backend type doesn't bring any persistence. But should be enough for PoC scenario.
YAPT also ships with SQLite based Backend which brings persistence.

## UI ##
There is a very simple WebUI, which gives overview of already provisioned devices and provisioning status of new devices.

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

# YAPT #

## Starting / stopping services ##
Yapt needs rabbitmq server to be started prior to yapt service. This is Linux platform specific which could be done using Linux init scripts under __/etc/init.d__ or on systemd based systems with __systemctl__ or __service__ commands.
YAPT ships with a start / stop script called __yapt.sh__.
* __yapt.sh start__ starts yapt
* __yapt.sh stop__ stops yapt

## Logging ##

* YAPT writes log information into
    - logs/info.log (informational)
    - logs/error.log (debug)
* A __tail -f info.log | grep PROV__ will show each provsioning tasks status.

## WebUI ##
Default WebUI URL is __http://<<ip>>:8080/yapt__

# Installation #

## Standalone ##

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

#### User and Passwords ####
YAPT needs following password generated before started first time:

- Create AMQP bus user and password

  * Start rabbitmq server using linux specific start scripts. "/etc/init.d/rabbitmq-server start on CentOS 6"
  * rabbitmqctl add_user yapt juniper123
  * rabbitmqctl set_user_tags yapt administrator
  * rabbitmqctl set_permissions -p / yapt ".*" ".*" ".*"

- Password Utility

YAPT ships with password utility, which is used to save encrypted passwords in YAPT configuration files. This tool can be started by following commands:

* cd lib/utils
* PYTHONPATH=__PATH_TO_YAPT_INSTALLATION__ /usr/local/bin/python2.7 ./password.py

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
First of all you need to create a master key. If there is already a master key this won't be overwritten and has to be deleted from master key file.

##### Device Authentication #####
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

## Docker ##

Running YAPT in docker environment consists of four basic containers: 
* Backend container
* UI container
* Task container
* Bus container

We will need a running docker installation to proceed with next steps. 
There is an install script in docker directory which could do the needed steps.

```
#!/bin/bash

#Build rabbitmq stuff
cd rabbitmq
docker build -t yapt-rabbitmq .
docker run -d --hostname yapt-rabbitmq --name yapt-rabbitmq -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=yapt -e RABBITMQ_DEFAULT_PASS=juniper123 yapt-rabbitmq

#Build YAPT yapt-base image

cd ..
cd yapt-base
docker build -t yapt-base-image .

#Build shared volume
cd ..
docker create -v /ds --name yapt-ds python:2 /bin/true
tar xvfz ../juniper-yapt-0.0.2.tar.gz
docker cp ../juniper-yapt-0.0.2 yapt-ds:/ds

#Start YAPT container

docker run -w /ds/juniper-yapt-0.0.2 -ti --volumes-from yapt-ds --name yapt-backend yapt-base-image python /ds/juniper-yapt-0.0.2/yaptbackend.py
docker run -w /ds/juniper-yapt-0.0.2 -ti -p 8080:8080 --volumes-from yapt-ds --name yapt-ui yapt-base-image python /ds/juniper-yapt-0.0.2/yaptui.py
docker run -w /ds/juniper-yapt-0.0.2 -p 443:443 -p 80:80 -p 7804:7804 -ti --volumes-from yapt-ds --name yapt-task yapt-base-image python /ds/juniper-yapt-0.0.2/yapttask.py

```

#### Configuration ####

- edit __conf/yapt/yapt.yml__ file under conf/yapt directory to fit your environment settings
  - Parameter __SourcePlugins__: Set the source plugin to the one you want to be used and configure source plugins settings under __Global Section__ in __yapt.yml__
  - Parameter __WebUiAddress__: should be set to interface IP WebUI will be reachable
  - If YAPT server operates behind NAT address we need to set:
  ```
  WebUiNat: False                                 #Enable YAPT WebUI being behind NAT
  WebUiNatIp: 172.30.162.52                       #NAT IP
  ```
  - Configure the services which have been enabled under __SourcePlugins__ section

- edit group file under __conf/groups__. YAPT supports building groups to apply specific tasks to devices. Here is an example for SRX devices.

```
---
#**********************************************************************************************************************
#GROUP: SRX
#***********************************************************************************************************************

########################################################################################################################
#Tasks Section (turn on/off provisioning tasks / configure specific task settings)
########################################################################################################################
TASKS:

  Provision:
    #Enable provision tasks and set processing order within sequence
    #Sequence: Init, Filecp, Software, Ipam, Configuration, Cert, Discovery, Policy, Assign, Rule, Publish, Cleanup
    Sequence: [Init, Filecp, Software, Configuration, Cleanup]

    Configuration:
      DeviceConfTemplateDir: conf/devices/template/   #device specific template config directory
      DeviceConfTemplateFile: srx_no_ipam.j2          #device config template name
      DeviceConfDataDir: conf/devices/data/           #device specific template data config directory
      DefaultConfDir: conf/devices/default/           #default config template file directory
      Merge: False                                    #Merge Configuration
      Overwrite: True                                 #Replace Configuration

      Internal:
        CommitTimeout: 120                            #Set Commit Timeout to x sec
        ConfirmedTimeout: 5                           #Set Commit confirmed timeout to x min

      Ansibleapi:
        Playbook: yapt_playbook.yml                   #Set Playbook file name. Playbooks stored in conf/ansible/playbook

    Cert:
      PortForwarding: False                                         #Enable Port Forwarding for cert retrieval
      LocalFwdPort: 5554                                            #Forwarding Port on device
      RemoteFwdHost: 10.15.115.2                                    #Remote host to forward to
      RemoteFwdHostPort: 8080                                       #Port on remote host to forward to
      EnrollmentUrl: ejbca/publicweb/apply/scep/advpn/pkiclient.exe #
      RevocationUrl: ejbca/publicweb/status/ocsp                    #

    Discovery:
      Mode: Discovery                                 #Set discovery mode to either Discovery or Configlet
      ConnectionConfigletDir: conf/configlet/         #modeled device configlet file path

    Filecp:
      Files: [ADVPNCertRollout.slax]                  #File(s) to be copied to device (e.g. SLAX)
      FileLocalDir: scripts/                          #source directory where to find files (defaults to script dir)
      FileRemoteDir: /var/db/scripts/event            #Event/Commit/OP Script or any other directory path on device

    Ipam:
      Module: nipap
      Address: 10.15.115.6
      Port: '1337'
      Prefixes: [10.200.0.0/24, 10.13.113.0/24]
      User: nipap
      Password: nipap

    Software:
      ImageDir: images/                               #device software images directory

      TargetVersion:
        FIREFLY-PERIMETER: 12.1X47-D35.2
        VSRX: 15.1X49-D100.6
        SRX100: 12.3X48-D40
        SRX110: 12.3X48-D40
        SRX210: 12.3X48-D40
        SRX220: 12.3X48-D40
        SRX300: 15.1X49-D70
        SRX320: 15.1X49-D70
        SRX340: 15.1X49-D70
        SRX345: 15.1X49-D70

########################################################################################################################
#Verification Task Section
########################################################################################################################
  Verification:
    Sequence: [Init, Cleanup]

    Ping:
      Destination: 10.12.111.1
      Count: '10'

    Vpn:
      SaRemoteAddress: 10.11.111.115

    Jsnap:
      Tests: [test_is_equal.yml]
```

Devices will be assigned to a group by setting group name in device data file under __conf/devices/data__. Here is an example:

```
yapt:
  location: local
  device_type: srx
  device_group: srx

device:
  hostname: vsrx08
  timezone: Europe/Berlin
  domain_name: mycompany.local
  ntp_server: 192.168.2.1
  encrypted_password: $1$AjvjSnDw$QrTngM5tI.IqliertjQhb/
  community: public
  interfaces:
  - name: fxp0
    description: mgmt
    family: inet
    address: dhcp
  - name: ge-0/0/0
    description: untrust
    unit: 0
    family: inet
    address: ipam
    mask: 24
  - name: ge-0/0/1
    description: trust
    family: inet
    address: 10.12.118.1/24
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
    subject: CN=vsrx08,OU=IT,O=MyCompany,L=Berlin,DC=mycompany.local,C=DE
    domain_name: vsrx08.mycompany.local
    enrollment_url: http://192.168.2.49:5554/ejbca/publicweb/apply/scep/advpn/pkiclient.exe
    oscp_url: http://10.13.113.2:5554/ejbca/publicweb/status/ocsp
    challenge_password: juniper123
    revocation_url: http://192.168.2.49:5554/ejbca/publicweb/status/ocsp

```

Group definition has to be set to group file name without file suffix __device_group: srx__.

#### Ansible Configuration Task ####

To use ansible as task in standalone mode you will need to install Ansible Junos role by running:

```
ansible-galaxy install Juniper.junos
```

#### Starting YAPT server ####

- ./yapt.sh start
- Open browser and point to URL: http://yapt-server-ip:8080/yapt

If the centralised approach will be used we need additional services like DHCP / TFTP server. Here some example configurations of those:

#### DHCP server (ISC DHCP) ####

```
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

```
service tftp
{
	disable	= no
	socket_type		= dgram
	protocol		= udp
	wait			= yes
	user			= root
	server			= /usr/sbin/in.tftpd
	server_args		= -s /var/lib/tftpboot -t 120 -v
	per_source		= 11
	cps			= 100 2
	flags			= IPv4
	log_type                = FILE /var/log/tftpd.log
}
```

#### TFTP server (dnsmasq) ####

```
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

```
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

* Management platform 15.1R3
* Security Director: 15.1R2
* Management platform 16.1
* Security Director: 16.2 (Only partial support e.g. no firewall rule creation)

# YAPT config file #

```
########################################################################################################################
# YAPT Global Section
########################################################################################################################
YAPT:
  SourcePlugins: [phs, tftp]                      #Source plugin list
  PwdFile: conf/yapt/masterkey.yml                #Stores masterkey
  DevicePwdIsRsa: False                           #use ssh rsa authentication
  DeviceUsr: root                                 #initial device provisioning user
                                                  #initial device provisioning user password
  DevicePwd: gAAAAABZVNJTusuvsiGEsIF8n94w_2IhIkTbQwcWWm52T8n63qlQ0Lt5RZhdn7knuzm4z4YuZuaqu-l8i1J-fduHumqRPf0Q8A==
  DeviceGrpFilesDir: conf/groups/                 #Map device to a provisioning group
  DeviceConfDataDir: conf/devices/data/           #device specific template data config directory
  Backend: sql                                    #Backend Type (internal / sql)
  ConnectionProbeTimeout: 90                      #initial connection probe timeout
  RebootProbeCounter: 30                          #How many times probing should be done
  RebootProbeTimeout: 30                          #wait n sec starting probing after device is rebooted
  LogFileDirectory: logs                          #directory to keep the logs
  StartWebUi: true                                #start web interface listening on port <WebUiPort>
  WebUiAddress: 172.16.146.1                      #Webserver IP Address (Used for WebSocket Client)
  WebUiPort: '8080'                               #Webserver Listener Port
  WebUiIndex: index.html                          #UI index file to load
  WebUiNat: False                                 #Enable YAPT WebUI being behind NAT
  WebUiNatIp: 172.30.162.52                       #NAT IP
  RestApiPort: '9090'                             #YAPT Rest Api Listener Port
  WorkerThreads: 10                               #Amount of task queue worker threads to be started

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
    DeviceID: abc123                                        #DMI Device ID
                                                            #DMI Shared Secret
    SharedSecret: gAAAAABZVk8RuO9DYNhx92zfV5yypeMzFMFIkeY2T8GHWeBYs-BqAH7_oaGI7ktDdc9pQkxN9jlQSTtfbluMj0FxT5xlAKbLYA==
    LocalConfigFile: conf/services/ossh/ossh.conf           #Contains mandatory options for device ssh deamon
    RemoteConfigFile: /mfs/var/etc/sshd_config_obssh.yapt   #SSH config file on device. For outbound-ssh should be "/mfs/var/etc/sshd_config_obssh.yapt"
    SigHubCmd: kill -HUP `cat /var/run/inetd.pid`           #Sig HUP inetd to re-read it's configuration

  Phs:
    ServiceBindAddress: 172.16.146.1                        #SSL Server bind address
    ServiceListenPort: 8082                                 #SSL Server listen port
    InitConfPath: conf/services/phs/                        #Inital bootstrap config file
    EnableSSL: false                                        #HTTP or HTTPS used by PHC connection
    SSLCertificate: conf/yapt/ssl/cert.pem                  #SSL Certificate
    SSLPrivateKey: conf/yapt/ssl/privkey.pem                #SSL Private Key
    DeviceAuthFile: conf/services/phs/dev_auth              #device authentication by serial number

########################################################################################################################
#Junos Space Section
########################################################################################################################
JUNOSSPACE:
  Enabled: True                                     #Enable / disable Junos Space Connector (True / False)
  Version: space151                                 #Junos Space Version (space151 / space161)
  Ip: 10.17.117.101                                 #Junos Space IP address
  User: rest                                        #Junos Space REST API user
                                                    #Junos Space REST API user password
  Password: gAAAAABZd847ljdieMlNqwcxA2b0fFQUZKc6euz0H_d1LodcRLmEDge436haLJgBNpQDyYEv76hcXXNGdE7U9NONF3X5bYyXhw==
  DeviceAddMethod: Discovery                        #Configlet or Discovery
  TemplateDir: conf/space/templates/151/            #Junos Space REST API Templates (must be right Junos Space version)
  ConnectionConfigletDir: conf/configlet/           #modeled device configlet files
  RestTimeout: 5                                    #Junos Space Wait n sec for next rest call

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
  AMQPAddress: 127.0.0.1
  AMQPType: direct
  User: yapt
  Password: gAAAAABZXKh1cacgc1qPE7Bc2JPcI_G0_2QaGEyr0Yu_6kIoKuVngbRBWcCuzAMrU3hKF0eSDG4lif6WpJdv0upwfWbS5eU70w==

########################################################################################################################
#Logging Related Stuff
########################################################################################################################

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
    * __configlet__: keeps configuration / template files if rapid deployment (outbount-ssh) wiht Junos Space is used
    * __devices__: keeps device specific configuration / templates
    * __groups__: keeps device group related configuration files
    * __plugins__: keeps source plugin description files
    * __services__: keeps service configuration / related files
    * __space__: keeps Junos Space related files
    * __yapt__: keeps yapt config file (yapt.yml)
    * __jsnapy__ keeps jsnapy related files
7. __lib__: YAPT libraries
    * __amqp__: amqp bus
    * __backend__: internal / sql
    * __plugins__: source plugins
    * __services__: services (OSSH / PHS / FILE)
    * __tasks__: provisioning tasks / verification tasks
    * __templates__: template file for provisioning stuff
    * __utils__: currently password manager
    * __web__: web related files (REST API / UI)
