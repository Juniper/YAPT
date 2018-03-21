# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Author: cklewar


import re
import requests
import gitlab
import yaml

from jinja2 import Environment, BaseLoader, TemplateNotFound
from lib.config.source import DeviceConfigSource
import lib.constants as c
from lib.logmsg import LogGit as logmsg
from lib.tools import Tools


class Cgitlab(DeviceConfigSource):

    def __init__(self):
        super(Cgitlab, self).__init__()
        self.session = None
        self.gl = None

    def create_conn(self):

        URL = '{0}://{1}:{2}'.format(c.conf.SOURCE.Cgitlab.Protocol, c.conf.SOURCE.Cgitlab.Address,
                                     c.conf.SOURCE.Cgitlab.Port)
        SIGN_IN_URL = '{0}{1}'.format(URL, c.conf.SOURCE.Cgitlab.LoginUrl)
        LOGIN_URL = '{0}{1}'.format(URL, c.conf.SOURCE.Cgitlab.LoginUrl)

        self.session = requests.Session()
        m = None
        sign_in_page = self.session.get(SIGN_IN_URL).content

        for l in sign_in_page.split('\n'):

            m = re.search('name="authenticity_token" value="([^"]+)"', l)
            if m:
                break

        token = None

        if m:
            token = m.group(1)

        if not token:
            Tools.create_log_msg(self.name, None, 'Unable to find the authenticity token')
            return False, None

        data = {'user[login]': c.conf.SOURCE.Cgitlab.User,
                'user[password]': c.conf.SOURCE.Cgitlab.Password,
                'authenticity_token': token}
        r = self.session.post(LOGIN_URL, data=data)

        if r.status_code != 200:
            Tools.create_log_msg(self.name, None, 'Login to <{0}> failed'.format(URL))
            return False, None
        else:
            self.gl = gitlab.Gitlab(URL, api_version='4', session=self.session)
            return True, None

    def get_config_template_file(self, serialnumber, grp_cfg):
        return False, None

    def get_config_template_data(self, serialnumber, grp_cfg):
        self.create_conn()
        project = self.gl.projects.get(c.conf.SOURCE.Cgitlab.DevCfgTemplate)
        oid = False

        for d in project.repository_tree():

            if d['name'] == grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile:
                oid = d['id']

        template = Environment(loader=BaseLoader).from_string(project.repository_raw_blob(oid))
        self.session.close()
        return True, template

    def add_config_template_data(self, templateName=None, templateData=None, group=None):
        pass

    def del_config_template_data(self, templateName=None, group=None):
        pass

    def get_bootstrap_config_template(self, serialnumber, path, file):
        self.create_conn()
        project = self.gl.projects.get(c.conf.SOURCE.Cgitlab.VnfBoostrapTemplate)
        oid = [d['id'] for d in project.repository_tree() if d['name'] == file][0]
        template = Environment(loader=BaseLoader).from_string(project.repository_raw_blob(oid))
        self.session.close()
        return True, template

    def get_config_data_file(self, serialnumber, deviceOsshId):
        return False, None

    def get_config_data(self, serialnumber=None, deviceOsshId=None):

        resp = self.create_conn()

        if resp:
            project = self.gl.projects.get(c.conf.SOURCE.Cgitlab.DevCfg)
            oid = False

            for d in project.repository_tree():
                if d['name'] == serialnumber + '.yml':
                    oid = d['id']

            if oid:

                try:

                    datavars = yaml.safe_load(project.repository_raw_blob(oid))
                    self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                          logmsg.GIT_DEV_CFG_OK.format(serialnumber + '.yml')))
                    self.session.close()
                    return True, datavars

                except yaml.YAMLError as exc:
                    self.logger.info(
                        '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                       serialnumber if serialnumber else deviceOsshId,
                                                                                       serialnumber + '.yml',
                                                                                       exc))
                    self.session.close()
                    return False, None

            else:
                self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                      logmsg.GIT_DEV_CFG_NOK.format(serialnumber)))
        else:
            pass

    def get_group_data_file(self, serialnumber, group):
        return False, None

    def get_group_data(self, serialnumber, group):
        self.create_conn()
        project = self.gl.projects.get(c.conf.SOURCE.Cgitlab.DevGrpCfg)

        oid = [d['id'] for d in project.repository_tree() if d['name'] == group + '.yml'][0]

        try:

            datavars = yaml.safe_load(project.repository_raw_blob(oid))
            self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                  logmsg.GIT_DEV_GRP_CFG_OK.format(serialnumber + '.yml')))
            self.session.close()
            return True, datavars

        except yaml.YAMLError as exc:
            self.logger.info(
                '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                               serialnumber,
                                                                               serialnumber + '.yml',
                                                                               exc))
            self.session.close()
            return False, None

    def add_group_data(self, groupName=None, groupData=None):
        pass

    def del_group_data(self, groupName=None):
        pass
