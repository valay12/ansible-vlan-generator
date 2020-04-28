#!/usr/bin/python

class FilterModule(object):
  def filters(self):
    return {
      'expand_vlans': self.expand_vlans,
      'a_filter': self.a_filter
    }

  def expand_vlans(self, vlan_range):
    try:
      if isinstance(vlan_range, int):
        return [vlan_range]
      elif ',' in vlan_range:
        vlan_list = []
        for i in vlan_range.split(','):
          if '-' in i:
            (start, end) = i.split('-')
            (start, end) = (int(start), int(end))
            vlan_list = vlan_list + list(range(start,end+1))
          else:
            vlan_list.append(int(i))
        return vlan_list
      elif '-' in vlan_range:
        (start, end) = vlan_range.split('-')
        (start, end) = (int(start), int(end))
        return list(range(start,end+1))
      else:
        return [int(vlan_range)]
    except:
      return 'error'

  def a_filter(self, a_variable):
    return a_variable + '123'
