# About #
YAPT (Yet Another Provisioning Tool) is for provisioning SRX / EX / NFX device. It's main goal is to deliver Zero Touch Provisioning.

YAPT runs with **Python 2 (2.7+)**.

# Documentation #

YAPT documentation with more detailed installation instructions can be found in local Wiki at [YAPT DOC].

[YAPT DOC]: https://git.juniper.net/cklewar/YAPT/wikis/home

# INSTALLATION #

## Linux box ##
- To run YAPT we need a linux box, which could be CentOS 6/7 or Ubuntu 14.04

## Python ##
- YAPT needs Python 2.7 to be installed
- To install YAPT it is good to have Python "pip" installed

## rabbitmq ##
- Install rabbitmq according to <https://www.rabbitmq.com/install-rpm.html>
- If not already exists create a file under __/etc/rabbitmq/__ called __rabbitmq.config__. Put following lines into file. This will turn of heartbeat, which is not being used by YAPT.
```
[
    {rabbit, [{tcp_listeners, [5672]}, {heartbeat, 0}]}
].
```

## YAPT ##
- git clone https://git.juniper.net/cklewar/yapt.git
- cd YAPT
- pip install -r requirements.txt
- edit __conf/yapt/yapt.yml__ file in conf directory to fit your environment settings (have a look at the wiki page for the various options)
  - Parameter __SourcePlugins__: Set the source plugin to the one you want to be used and configure source plugin settings under __Global Settings__ section in __yapt.yml__
  - Parameter __WebUiAddress__: should be set to interface IP WebUI will be reachable
- Start rabbitmq server using linux specific start scripts. "/etc/init.d/rabbitmq-server start on CentOS 6"
- ./yapt.sh start
- Open browser and point to URL: http://yapt-server-ip:8080/yapt

# LIBS / TOOLS #
* rabbitmq
* IscDhcpLeases
* CherryPy
* ws4py
* jinja2
* watchdog
* junos-eznc
* requests
* PyYAML
* pika
* pynipap
* ruamel.yaml
* jsonpickle
* ansible

# CONTRIBUTORS #
  - Christian Klewar (cklewar@juniper.net)
