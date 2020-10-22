#!/usr/bin/python
# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible.module_utils.six.moves.urllib.error import HTTPError

import os
import requests
import re

class Connection:

  def __init__(self, vm_cluster, username, password):
    self.vm_cluster - vm_cluster
    self.username = username
    self.password = password
    
  def load_data(self, db, params=None):
    env = os.getenv('at_env')
    if env.upper = 'DEV':
      url = 'https://example-dev.com'
    elif env.upper = 'UAT':
      url = 'https://example-uat.com'
    elif env.upper = 'PROD':
      url = 'https://example.com'
    url = url + '/services/reports/{}'.format(db)
    
    headers = {'Content-type': 'application/json'}
    auth = (self.username, self.password)
    proxies = {'http': '', 'https': ''}
    verify = '/etc/pki/cert.pem'
    
    try:
      response = requests.get(url,
                              auth=auth,
                              proxies=proxies,
                              timeout=30,
                              headers=headers,
                              params=params,
                              verify=verify)
      response.raise_for_status()
      
    except HTTPError as e:
      raise AnsibleError('API error:{}'.format(e.reason))
    return response.json()['data']
    
class ActionModule(ActionBase):

  def __init__(self, *args, **kwargs):
    super(ActionModule, self).__init__(*args, **kwargs)
    
  def _get_interface_list(self, conn):
    id = '123'
    params = {'Description': '*' + conn.vm_cluster + '*'}
    
    data = conn.load_data(id, params)
    if len(data) < 1:
      raise AnsibleError('No interfaces found matching description {}'.format(conn.vm_cluster))
    return data
    
  def _compile(self, conn, interface_report):
    id = '123'
    device_dict = {}
    output = {}
    for interface in interface_report:
      description = interface['description']
      if re.match('.*\+Mgmt$', description, re.IGNORECASE) or re.match('.*R$', description, re.IGNORECASE):
        continue
        
      device_id = str(interface['device_id'])
      tmp_dict = {'interface': interface['name'],
                  'description': description}
      
      if device_id not in device_dict.keys():
        params = {'id': device_id}
        device_data = conn.load_data(id, params)
        
        if len(device_data) != 1:
          raise AnsibleError('Multiple devices found for ID: {}'.format(device_id))
        else:
          hostname = device_data[0]['hostname']
          device_dict[device_id] = hostname
          output[hostname] = [tmp_dict]
      else:
        hostname = device_dict[device_id]
        if tmp_dict['description'] < output[hostname][0]['description']:
          output[hostname].insert(0, tmp_dict)
        else:
          output[hostname].append(tmp_dict)
    return output, sorted(device_dict.values())
    
  def run(self, tmp=None, task_vars=None):
    result = super(ActionModule, self).run(tmp, task_vars)
    
    conn = Connection(vm_cluster = self._task.args['name'],
                      username = 'admin',
                      password = 'password')
    interface_report = self._get_interface_list(conn)
    output, device_list = self._compile(conn, interface_report)
    
    result = {'changed': False,
              'output': output,
              'device_list': device_list}
    return result
