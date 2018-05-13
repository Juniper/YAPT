# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
# Copyright (c) 2018 Juniper Networks, Inc.
# All rights reserved.
# Use is subject to license terms.
#
# Author: cklewar


import re
import requests
import gitlab
import yaml
import lib.constants as c
import json

from requests.exceptions import ConnectionError
from gitlab.exceptions import GitlabError, GitlabDeleteError, GitlabConnectionError, GitlabCreateError
from jinja2 import Environment, BaseLoader
from lib.storage.base import Storage
from lib.logmsg import LogGit as logmsg
from lib.tools import Tools


class Cgitlab(Storage):

    def __init__(self):
        super(Cgitlab, self).__init__()
        self.session = None
        self.gl = None

    def authenticate_cookie(self):

        URL = '{0}://{1}:{2}'.format(c.conf.STORAGE.Cgitlab.Protocol, c.conf.STORAGE.Cgitlab.Address,
                                     c.conf.STORAGE.Cgitlab.Port)
        SIGN_IN_URL = '{0}{1}'.format(URL, c.conf.STORAGE.Cgitlab.LoginUrl)
        LOGIN_URL = '{0}{1}'.format(URL, c.conf.STORAGE.Cgitlab.LoginUrl)

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

        data = {'user[login]': c.conf.STORAGE.Cgitlab.User,
                'user[password]': c.conf.STORAGE.Cgitlab.Password,
                'authenticity_token': token}

        try:
            r = self.session.post(LOGIN_URL, data=data)

        except ConnectionError as ce:
            self.logger.info(Tools.create_log_msg(self.name, None, 'Connection error: <{0}>'.format(ce.message)))
            return False, 'Connection error: <{0}>'.format(ce.message)

        if r.status_code != 200:
            Tools.create_log_msg(self.name, None, 'Login to <{0}> failed'.format(URL))
            return False, None
        else:
            self.gl = gitlab.Gitlab(URL, api_version='4', session=self.session)
            return True, None

    def authenticate_oauth(self):

        URL = '{0}://{1}:{2}'.format(c.conf.STORAGE.Cgitlab.Protocol, c.conf.STORAGE.Cgitlab.Address,
                                     c.conf.STORAGE.Cgitlab.Port)
        LOGIN_URL = '{0}{1}'.format(URL, c.conf.STORAGE.Cgitlab.LoginUrl)

        payload = {
            "grant_type": "password",
            "username": c.conf.STORAGE.Cgitlab.User,
            "password": c.conf.STORAGE.Cgitlab.Password
        }
        headers = {
            'content-type': "application/json",
            'cache-control': "no-cache"
        }

        try:

            self.logger.debug(Tools.create_log_msg(self.name, None, "POST {0}, {1}, {2}".format(LOGIN_URL, payload, headers)))
            response = requests.request("POST", LOGIN_URL, data=json.dumps(payload), headers=headers)

        except ConnectionError as ce:
            self.logger.info(Tools.create_log_msg(self.name, None, 'Connection error: <{0}>'.format(ce.message)))
            return False, 'Connection error: <{0}>'.format(ce.message)

        if response.status_code == 200:
            resp = json.loads(response.content)
            self.logger.debug(Tools.create_log_msg(self.name, None, resp))

            if 'access_token' in resp:

                access_token = resp['access_token']
                self.gl = gitlab.Gitlab(URL, oauth_token=access_token)
                return True, logmsg.GIT_AUTH_OK
            else:
                self.logger.info(Tools.create_log_msg(self.name, None, logmsg.GIT_AUTH_ACCESS_TOKEN_NOK))
                return False, logmsg.GIT_AUTH_NOK
        else:
            self.logger.debu(Tools.create_log_msg(self.name, None, response.status_code))
            self.logger.debug(Tools.create_log_msg(self.name, None, response.headers))
            self.logger.debug(Tools.create_log_msg(self.name, None, response))
            self.logger.info(Tools.create_log_msg(self.name, None, logmsg.GIT_AUTH_NOK))
            return False, logmsg.GIT_AUTH_NOK

    def get_config_template_file(self, serialnumber=None, templateName=None, groupName=None):

        if serialnumber is not None:

            status, data = self.get_config_template_data(serialnumber=serialnumber, templateName=templateName, isRaw=True)
            path = 'tmp/'

            if status:
                with open(path + templateName, 'w') as fp:
                    fp.write(data)
                return True, path + templateName
            else:
                return False, path + templateName

    def get_config_template_data(self, serialnumber=None, templateName=None, groupName=None, isRaw=None):

        auth_status, data = self.authenticate_oauth()

        if auth_status:

            if groupName:

                status, groupData = self.get_group_data(serialnumber=serialnumber, groupName=groupName, isRaw=False)

                if status:

                    grp_cfg = Tools.create_config_view(config_type=c.CONFIG_TYPE_GROUP, stream=groupData)
                    template_file = grp_cfg.TASKS.Provision.Configuration.DeviceConfTemplateFile

                    try:
                        project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgTemplate)
                        path = '{0}'.format(template_file)

                    except (GitlabConnectionError, GitlabError) as gle:
                        return False, 'Failed to get project with error: <0>'.format(gle.message)

                    try:
                        f = project.files.get(file_path=path, ref='master')
                    except GitlabError as ge:
                        return False, 'Failed to get template config with error: <{0}>'.format(ge.message)

                    if isRaw:
                        return True, f.decode()
                    else:

                        try:
                            template = Environment(loader=BaseLoader).from_string(f.decode())
                            return True, template

                        except TypeError as te:
                            return False, te.message
                else:
                    return False, groupData
            else:

                try:
                    project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgTemplate)
                    path = '{0}'.format(templateName)

                except (GitlabConnectionError, GitlabError) as gle:
                    return False, 'Failed to get project with error: <0>'.format(gle.message)

                try:
                    f = project.files.get(file_path=path, ref='master')
                except GitlabError as ge:
                    return False, 'Failed to get template config with error: <{0}>'.format(ge.message)

                if isRaw:
                    return True, f.decode()
                else:

                    try:

                        template = Environment(loader=BaseLoader).from_string(f.decode())
                        return True, template

                    except TypeError as te:
                        return False, te.message
        else:
            return auth_status, data

    def add_config_template_data(self, templateName=None, templateData=None, groupName=None):

        status, data = self.authenticate_oauth()

        if status:
            try:
                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgTemplate)
                file_path = templateName + c.CONFIG_FILE_SUFFIX_TEMPLATE

                file_body = {
                    "file_path": file_path,
                    "branch": "master",
                    "content": templateData,
                    "commit_message": "Device template {0}".format(templateName)
                }

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            try:
                f = project.files.create(file_body)
                return status, f
            except GitlabCreateError as gce:
                return False, 'Failed to add device template config with error: <{0}>'.format(gce.message)
        else:
            return status, data

    def del_config_template_data(self, templateName=None, groupName=None):

        status, data = self.authenticate_oauth()

        if status:
            try:
                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgTemplate)
                file_path = '{0}{1}'.format(templateName, c.CONFIG_FILE_SUFFIX_TEMPLATE)
            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            try:
                f = project.files.get(file_path=file_path, ref='master')
            except GitlabError as ge:
                return False, 'Failed to get template config with error: <{0}>'.format(ge.message)

            try:
                f.delete(branch='master', commit_message='Delete device template {0}'.format(file_path))
                return status, 'Successfully deleted template {0}'.format(file_path)
            except GitlabDeleteError as gde:
                return False, 'Failed to delete template config with error: <{0}>'.format(gde.message)
        else:
            return status, data

    def get_bootstrap_config_template(self, serialnumber=None, path=None, file=None):
        self.authenticate_oauth()
        project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.VnfBoostrapTemplate)
        oid = [d['id'] for d in project.repository_tree() if d['name'] == file][0]
        template = Environment(loader=BaseLoader).from_string(project.repository_raw_blob(oid))
        self.session.close()
        return True, template

    def get_device_config_data_file(self, serialnumber=None, deviceOsshId=None):

        if serialnumber is not None:
            status, data = self.get_device_config_data(serialnumber=serialnumber, isRaw=True)
            path = 'tmp/'
            file_name = serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE

            if status:
                with open(path + file_name, 'w') as fp:
                    fp.write(data)
                return True, serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE
            else:
                return False, path + file_name

    def get_device_config_data(self, serialnumber=None, isRaw=None):

        status, data = self.authenticate_oauth()

        if status:

            try:

                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfg)
                file_path = '{0}{1}'.format(serialnumber, c.CONFIG_FILE_SUFFIX_DEVICE)

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            try:

                f = project.files.get(file_path=file_path, ref='master')

            except GitlabError as ge:
                return False, 'Failed to get device config with error: <{0}>'.format(ge.message)

            if isRaw:

                return True, f.decode()

            else:

                try:

                    datavars = yaml.safe_load(f.decode())
                    self.logger.info(Tools.create_log_msg(self.name, serialnumber,
                                                          logmsg.GIT_DEV_CFG_OK.format(
                                                              serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE)))
                    return True, datavars

                except yaml.YAMLError as exc:
                    self.logger.info(
                        '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                       serialnumber,
                                                                                       serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE,
                                                                                       exc))
                    return False, self.logger.info(
                        '{0}-[{1}]: Error in loading config file <{2}> --> {3}'.format(self.name,
                                                                                       serialnumber,
                                                                                       serialnumber + c.CONFIG_FILE_SUFFIX_DEVICE,
                                                                                       exc))
        else:
            return status, data

    def add_device_config_data(self, configSerial=None, configData=None):

        status, data = self.authenticate_oauth()

        if status:

            try:

                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfg)
                file_path = configSerial + c.CONFIG_FILE_SUFFIX_DEVICE

                file_body = {
                    "file_path": file_path,
                    "branch": "master",
                    "content": configData,
                    "commit_message": "Device config {0}".format(configSerial)
                }

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            try:
                f = project.files.create(file_body)
                return status, f

            except GitlabCreateError as gce:
                return False, 'Failed to add device config with error: <{0}>'.format(gce.message)
        else:
            return status, data

    def del_device_config_data(self, configSerial=None):

        status, data = self.authenticate_oauth()

        if status:

            try:

                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfg)
                file_path = '{0}{1}'.format(configSerial, c.CONFIG_FILE_SUFFIX_DEVICE)

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <{0}>'.format(gle)

            try:

                f = project.files.get(file_path=file_path, ref='master')

            except GitlabError as ge:
                return False, 'Failed to delete device config with error: <{0}>'.format(ge.message)

            try:

                f.delete(branch='master', commit_message='Delete device config {0}'.format(file_path))
                return True, 'Successfully deleted device config {0}'.format(file_path)

            except GitlabDeleteError as gde:
                return False, 'Failed to delete device config with error: <{0}>'.format(gde.message)

        else:
            return status, data

    def get_group_data_file(self, serialnumber=None, group=None):
        return False, None

    def get_group_data(self, serialnumber=None, groupName=None, isRaw=None):

        status, data = self.authenticate_oauth()

        if status:

            try:

                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgGrp)
                file_path = '{0}{1}'.format(groupName, c.CONFIG_FILE_SUFFIX_GROUP)

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            try:
                f = project.files.get(file_path=file_path, ref='master')
            except GitlabError as ge:
                return False, 'Failed to get group config with error: <{0}>'.format(ge.message)

            if isRaw:

                return True, f.decode()
            else:

                try:

                    datavars = yaml.safe_load(f.decode())
                    return True, datavars

                except yaml.YAMLError as exc:
                    self.logger.info(
                        '{0}-[{1}]: Error in loading group file <{2}> --> {3}'.format(self.name,
                                                                                      serialnumber,
                                                                                      groupName + c.CONFIG_FILE_SUFFIX_GROUP,
                                                                                      exc))
                    return False, '{0}-[{1}]: Error in loading group file <{2}> --> {3}'.format(self.name,
                                                                                                serialnumber,
                                                                                                groupName + c.CONFIG_FILE_SUFFIX_GROUP,
                                                                                                exc)
        else:
            return status, data

    def add_group_data(self, groupName=None, groupData=None):

        status, data = self.authenticate_oauth()

        if status:

            try:

                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgGrp)
                file_path = '{0}{1}'.format(groupName, c.CONFIG_FILE_SUFFIX_GROUP)

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            file_body = {
                "file_path": file_path,
                "branch": "master",
                "content": groupData,
                "commit_message": "Device group {0}".format(groupName)
            }

            try:

                f = project.files.create(file_body)
                return True, f

            except GitlabCreateError as gce:
                return False, 'Failed to add device group config with error: <{0}>'.format(gce.message)
        else:
            return status, data

    def del_group_data(self, groupName=None):

        status, data = self.authenticate_oauth()

        if status:

            try:
                project = self.gl.projects.get(c.conf.STORAGE.Cgitlab.DevCfgGrp)
                file_path = '{0}{1}'.format(groupName, c.CONFIG_FILE_SUFFIX_GROUP)

            except (GitlabConnectionError, GitlabError) as gle:
                return False, 'Failed to get project with error: <0>'.format(gle.message)

            try:
                f = project.files.get(file_path=file_path, ref='master')
            except GitlabError as ge:
                return False, 'Failed to get group config with error: <{0}>'.format(ge.message)

            try:
                f.delete(branch='master', commit_message='Delete device group {0}'.format(file_path))
                return status, 'Successfully deleted device group {0}'.format(file_path)
            except GitlabDeleteError as gde:
                return False, 'Failed to delete group config with error: <{0}>'.format(gde.message)
        else:
            return status, data
