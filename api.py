#!/usr/bin/python
"""
A Python library to perform low-level Linode API functions.

Copyright (c) 2008 Timothy J Fontaine <tjfontaine@gmail.com>
Copyright (c) 2008 James C Sinclair <james@irgeek.com>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import urllib
import urllib2
import simplejson


class MissingRequiredArgument(Exception):
  """Raised when a required parameter is missing."""
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiError(Exception):
  """Raised when a Linode API call returns an error."""
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiInfo:
  valid_commands = {}
  valid_params   = {}

LINODE_API_URL = 'https://beta.linode.com/api/'

class Api:
  def __init__(self, key, debug=False, batching=False):
    self.__key = key
    self.__urlopen = urllib2.urlopen
    self.__request = urllib2.Request
    self.__debug = debug
    self.__batching = batching
    self.__batch_cache = []

  @staticmethod
  def valid_commands():
    return ApiInfo.valid_commands.keys()

  @staticmethod
  def valid_params():
    return ApiInfo.valid_params.keys()

  def debugging(self, value = None):
    if value is not None:
      self.__debug = value

    return self.__debug

  def debug(self, msg):
    if self.__debug:
      print msg

  def batching(self, value = None):
    if value is not None:
      self.__batching = value

    return self.__batching

  def batchFlush(self):
    if not self.__batching:
      raise Exception('Cannot flush requests when not batching')

    json = simplejson.dumps(self.__batch_cache)
    self.__batch_cache = []
    request = { 'action' : 'batch', 'requestArray' : json }
    return self.__send_request(request)

  def __send_request(self, request):
    request['api_key'] = self.__key
    request['api_resultFormat'] = 'json'
    request = urllib.urlencode(request)
    self.debug('Sending '+request)
    req = self.__request(LINODE_API_URL, request)
    response = self.__urlopen(req)
    response = response.read()
    self.debug('Received '+response)
    try:
      json = simplejson.loads(response)
    except Exception, ex:
      print response
      raise ex

    if type(json) is dict:
      if len(json['ERRORARRAY']) > 0:
        raise ApiError(json['ERRORARRAY'])
      else:
        return json['DATA']
    else:
      return json

  def __api_request(required = [], optional = []):
    for k in required:
      k = k.lower()
      if not ApiInfo.valid_params.has_key(k):
        ApiInfo.valid_params[k] = True

    for k in optional:
      k = k.lower()
      if not ApiInfo.valid_params.has_key(k):
        ApiInfo.valid_params[k] = True

    def decorator(func):
      if not ApiInfo.valid_commands.has_key(func.__name__):
        ApiInfo.valid_commands[func.__name__] = True

      def wrapper(self, mparams = {}, *__args ,**__kw):
        request = {'api_action' : func.__name__.replace('_', '.')}

        if len(mparams) == 0: #only self, no passed parameters
          params = __kw
        else: #parameters passed, expect a dict
          params = mparams

        params = dict([(key.lower(),value) for key,value in params.iteritems()])

        for k in required:
          k = k.lower()

          if not params.has_key(k):
            raise MissingRequiredArgument(k)

        for k in params:
          k = k.lower()
          request[k] = params[k]

        result = func(self, request)
        if result is not None:
          request = result

        if self.__batching:
          self.__batch_cache.append(request)
          self.debug('Batched: '+simplejson.dumps(request))
        else:
          return self.__send_request(request)

      wrapper.__name__ = func.__name__
      wrapper.__doc__ = func.__doc__
      wrapper.__dict__.update(func.__dict__)
      return wrapper
    return decorator

  @__api_request(optional=['LinodeID'])
  def linode_list(self, request):
    pass

  @__api_request(required=['LinodeID'], optional=['Label',
                                                  'lpm_displayGroup',
                                                  'Alert_cpu_enabled',
                                                  'Alert_cpu_threshold',
                                                  'Alert_diskio_enabled',
                                                  'Alert_diskio_threshold',
                                                  'Alert_bwin_enabled',
                                                  'Alert_bwin_threshold',
                                                  'Alert_bwout_enabled',
                                                  'Alert_bwout_threshold',
                                                  'Alert_bwquota_enabled',
                                                  'Alert_bwquota_threshold',
                                                  'backupWindow',
                                                  'backupWeeklyDay',
                                                  'watchdog',
                                                 ])
  def linode_update(self, request):
    pass

  @__api_request(required=['DatacenterID', 'PlanID', 'PaymentTerm'])
  def linode_create(self, request):
    pass

  @__api_request(required=['LinodeID'])
  def linode_shutdown(self, request):
    pass

  @__api_request(required=['LinodeID'], optional=['LinodeConfigID'])
  def linode_boot(self, request):
    pass

  @__api_request(required=['LinodeID'])
  def linode_delete(self, request):
    pass

  @__api_request(required=['LinodeID'], optional=['LinodeConfigID'])
  def linode_reboot(self, request):
    pass

  @__api_request(required=['LinodeID'])
  def linode_config_list(self, request):
    pass

  @__api_request(required=['LinodeID', 'LinodeConfigID'], optional=[
                                                            'KernelID',
                                                            'Label',
                                                            'Comments',
                                                            'RAMLimit',
                                                            'DiskList',
                                                            'RunLevel',
                                                            'RootDeviceNum',
                                                            'RootDeviceCustom',
                                                            'RootDeviceRO',
                                                            'helper_disableUpdateDB',
                                                            'helper_xen',
                                                            'helper_depmod',
                                                          ])
  def linode_config_update(self, request):
    pass

  @__api_request(required=['LinodeID', 'KernelID', 'Label', 'Disklist'],
                                                 optional=[
                                                            'Comments',
                                                            'RAMLimit',
                                                            'RunLevel',
                                                            'RootDeviceNum',
                                                            'RootDeviceCustom',
                                                            'RootDeviceRO',
                                                            'helper_disableUpdateDB',
                                                            'helper_xen',
                                                            'helper_depmod',
                                                          ])
  def linode_config_create(self, request):
    pass

  @__api_request(required=['LinodeID', 'LinodeConfigID'])
  def linode_config_delete(self, request):
    pass
  
  @__api_request(required=['LinodeID'])
  def linode_disk_list(self, request):
    pass

  @__api_request(required=['LinodeID', 'DiskID'], optional=['Label', 'isReadOnly'])
  def linode_disk_update(self, request):
    pass

  @__api_request(required=['LinodeID', 'Type', 'Size'], optional=['Label', 'isReadOnly'])
  def linode_disk_create(self, request):
    pass

  @__api_request(required=['LinodeID', 'DiskID'])
  def linode_disk_duplicate(self, request):
    pass

  @__api_request(required=['LinodeID', 'DiskID'])
  def linode_disk_delete(self, request):
    pass

  @__api_request(required=['LinodeID', 'DiskID', 'Size'])
  def linode_disk_resize(self, request):
    pass

  @__api_request(required=['LinodeID', 'DistributionID', 'rootPass', 'Label', 'Size'])
  def linode_disk_createfromdistribution(self, request):
    pass

  @__api_request(required=['LinodeID'], optional=['IPAddressID'])
  def linode_ip_list(self, request):
    pass

  @__api_request(required=['LinodeID'], optional=['pendingOnly'])
  def linode_job_list(self, request):
    pass

  @__api_request(optional=['isXen'])
  def kernel_list(self, request):
    pass

  @__api_request()
  def distribution_list(self, request):
    pass

  @__api_request()
  def datacenter_list(self, request):
    pass
