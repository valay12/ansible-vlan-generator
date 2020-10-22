#!/usr/bin/python
# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
  name: inv_plugin
  plugin_type: inventory
  short_description: Generates inventory of switches from cmdb
  description: Generates inventory of switches from cmdb and grouped based on function
  options:
    plugin:
      description: Name of plugin
      required: True
  '''

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError, AnsibleParserError
import requests
import os
import re

class InventoryModule(BaseInventoryPlugin):
  NAME = 'inv_plugin'
  
  def verify_file(self, path):
    '''Return true/false if file is valid'''
    if path.endswith('inventory.yml'):
      return True
    else:
      return False
  
  def _load_vars(self, host):
    hostname = host['hostname']
    mgmt_ip = host['mgmtip']
    self.inventory.set_variable(hostname, 'ansible_host', mgmt_ip)
    
    if 'Nexus' in host['model']:
      self.inventory.set_variable(hostname, 'ansible_network_os', 'nxos')
    elif 'Catalyst' in host['model']:
      self.inventory.set_variable(hostname, 'ansible_network_os', 'ios')
  
  def _classify(self, host, at_env):
    '''Add hosts to function-specific inventory groups'''
    hostname = host['hostname']
    if at_env.upper() == 'DEV' or at_env.upper() == 'UAT':
      self.inventory.add_host(host=hostname, group='zone_access')
      self._load_vars(host)
      
    elif at_env.upper() == 'PROD':
      if re.match('^\S+-access$', hostname):
        self.inventory.add_host(host=hostname, group='zone_access')
      elif re.match('^\S+-aggr$', hostname):
        self.inventory.add_host(host=hostname, group='zone_aggr')
      else:
        self.inventory.add_host(host=hostname, group='unknown')
      self._load_vars(host)
      
    else:
      raise Exception('Environment %s not supported" % at_env)
      
  def _download_inventory(self, url):
    username = 'admin'
    password = 'password'
    auth = (username, password)
    verify = '/etc/pki/cert.pem'
    response = requests.get(url,
                            auth=auth,
                            timeout=30,
                            verify=verify)
    response.raise_for_status()
    
    return response.json()
    
  def _load_inventory(self):
    '''Return hosts'''
    
    at_env = os.getenv('at_env')
    
    DEV_HOST = 'https://example-dev.com'
    DEV_ARGS = ['hostname=lab-switch']
    
    UAT_HOST = 'https://example-uat.com'
    UAT_ARGS = ['hostname=lab-switch']
    
    PROD_HOST = 'https://example.com'
    PROD_ARGS = ['status=production',
                 'type=switch',
                 'vendor=cisco']
                 
    if at_env.upper == 'DEV':
      URL_HOST = DEV_HOST
      URL_ARGS = DEV_ARGS
    elif at_env.upper == 'UAT':
      URL_HOST = UAT_HOST
      URL_ARGS = UAT_ARGS
    elif at_env.upper == 'PROD':
      URL_HOST = PROD_HOST
      URL_ARGS = PROD_ARGS
    else:
      raise Exception("Environment %s not supported" % at_env)
      
    URL = URL_HOST + '/reports/cmdb.json?' + '&'.join(URL_ARGS)
    
    data = self._download_inventory(URL)
    if not data['data']:
      raise Exception('No data found')
      
    self.inventory.add_group('switches')
    self.inventory.set_variable('switches', 'ansible_connection', 'network_cli')
    
    self.inventory.add_group('zone_access')
    self.inventory.add_child('switches', 'zone_access')
    
    self.inventory.add_group('zone_aggr')
    self.inventory.add_child('switches','zone_aggr')
    
    self.inventory.add_group('unknown')
    self.inventory.add_group('switches, 'unknown')
    
    for host in data['data']:
      self._classify(host, at_env)
      
    localvars = {'ansible_connection': 'local'}
    self.inventory.add_group('local')
    self.inventory.add_host(host='localhost', group='local')
    for k, v in localvars.items():
      self.inventory.set_variable('local', k, v)
      
  def parse(self, inventory, loader, path, cache):
    '''Return dynamic inventory from source'''
    super(InventoryModule, self).parse(inventory, loader, path, cache)
    
    self._read_config_data(path)
    
    try:
      self.plugin = self.get_option('plugin')
    except Exception as e:
      raise AnsibleParserError('All options required: {}'.format(e))
      
    self._load_inventory()
