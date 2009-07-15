#!/usr/bin/python
"""
A Python library to perform low-level Linode API functions.

Copyright (c) 2009 Timothy J Fontaine <tjfontaine@gmail.com>
Copyright (c) 2009 Ryan Tucker <rtucker@gmail.com>
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

import logging
import urllib
import urllib2

try:
  import json
except:
  import simplejson as json


class MissingRequiredArgument(Exception):
  """Raised when a required parameter is missing."""
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiError(Exception):
  """Raised when a Linode API call returns an error.

  Returns:
    [{u'ERRORCODE': Error code number,
      u'ERRORMESSAGE': 'Description of error'}]

  ErrorCodes that can be returned by any method, per Linode API specification:
    0: ok
    1: Bad request
    2: No action was requested
    3: The requested class does not exist
    4: Authentication failed
    5: Object not found
    6: A required property is missing for this action
    7: Property is invalid
    8: A data validation error has occurred
    9: Method Not Implemented
    10: Too many batched requests
    11: RequestArray isn't valid JSON or WDDX
    13: Permission denied
    30: Charging the credit card failed
    31: Credit card is expired
    40: Limit of Linodes added per hour reached
  """
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiInfo:
  valid_commands = {}
  valid_params   = {}

LINODE_API_URL = 'https://beta.linode.com/api/'

class LowerCaseDict(dict):
  def __init__(self, copy=None):
    if copy:
      if isinstance(copy, dict):
        for k,v in copy.items():
          dict.__setitem__(self, k.lower(), v)
      else:
        for k,v in copy:
          dict.__setitem__(self, k.lower(), v)

  def __getitem__(self, key):
    return dict.__getitem__(self, key.lower())

  def __setitem__(self, key, value):
    dict.__setitem__(self, key.lower(), value)

  def __contains__(self, key):
    return dict.__contains__(self, key.lower())

  def has_key(self, key):
    return dict.has_key(self, key.lower())

  def get(self, key, def_val=None):
    return dict.get(self, key.lower(), def_val)

  def setdefault(self, key, def_val=None):
    return dict.setdefault(self, key.lower(), def_val)

  def update(self, copy):
    for k,v in copy.items():
      dict.__setitem__(self, k.lower(), v)

  def fromkeys(self, iterable, value=None):
    d = self.__class__()
    for k in iterable:
      dict.__setitem__(d, k.lower(), value)
    return d

  def pop(self, key, def_val=None):
    return dict.pop(self, key.lower(), def_val)

class Api:
  """Linode API (version 2) client class.

  Instantiate with: Api(), or Api(optional parameters)

  Optional parameters:
        key - Your API key, from "My Profile" in the LPM (default: None)
        batching - Enable batching support (default: False)

  This interfaces with the Linode API (version 2) and receives a response
  via JSON, which is then parsed and returned as a dictionary (or list
  of dictionaries).

  In the event of API problems, raises ApiError:
        api.ApiError: [{u'ERRORCODE': 99,
                        u'ERRORMESSAGE': u'Error Message'}]

  If you do not specify a key, the only method you may use is
  user_getapikey(username, password).  This will retrieve and store
  the API key for a given user.

  Full documentation on the API can be found from Linode at:
        http://beta.linode.com/api/autodoc.cfm
  """

  def __init__(self, key=None, batching=False):
    self.__key = key
    self.__urlopen = urllib2.urlopen
    self.__request = urllib2.Request
    self.batching = batching
    self.__batch_cache = []

  @staticmethod
  def valid_commands():
    """Returns a list of API commands supported by this class."""
    return ApiInfo.valid_commands.keys()

  @staticmethod
  def valid_params():
    """Returns a list of all parameters used by methods of this class."""
    return ApiInfo.valid_params.keys()

  def batchFlush(self):
    """Initiates a batch flush.  Raises Exception if not in batching mode."""
    if not self.batching:
      raise Exception('Cannot flush requests when not batching')

    s = json.dumps(self.__batch_cache)
    self.__batch_cache = []
    request = { 'api_action' : 'batch', 'requestArray' : s }
    return self.__send_request(request)

  def __send_request(self, request):
    if self.__key:
      request['api_key'] = self.__key
    elif request['api_action'] != 'user.getapikey':
      raise Exception('Must call user_getapikey to fetch key')

    request['api_responseFormat'] = 'json'

    logging.debug('Parmaters '+str(request))
    request = urllib.urlencode(request)

    req = self.__request(LINODE_API_URL, request)
    response = self.__urlopen(req)
    response = response.read()

    logging.debug('Raw Response: '+response)

    try:
      s = json.loads(response)
    except Exception, ex:
      print response
      raise ex

    if isinstance(s, dict):
      s = LowerCaseDict(s)
      if len(s['ERRORARRAY']) > 0:
        raise ApiError(s['ERRORARRAY'])
      else:
        if s['ACTION'] == 'user.getapikey':
          self.__key = s['DATA']['API_KEY']
          logging.debug('API key is: '+self.__key)
        return s['DATA']
    else:
      return s

  def __api_request(required=[], optional=[]):
    """Decorator to define required and optional paramters"""
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

      def wrapper(self, **kw):
        request = LowerCaseDict()
        request['api_action'] = func.__name__.replace('_', '.')

        params = LowerCaseDict(kw)

        for k in required:
          if not params.has_key(k):
            raise MissingRequiredArgument(k)

        for k in params:
          request[k] = params[k]

        result = func(self, request)
        if result is not None:
          request = result

        if self.batching:
          self.__batch_cache.append(request)
          logging.debug('Batched: '+ json.dumps(request))
        else:
          return self.__send_request(request)

      wrapper.__name__ = func.__name__
      wrapper.__doc__ = func.__doc__
      wrapper.__dict__.update(func.__dict__)

      if (required or optional) and wrapper.__doc__:
        # Generate parameter documentation in docstring
        if len(wrapper.__doc__.split('\n')) is 1:  # one-liners need whitespace
          wrapper.__doc__ += '\n'
        wrapper.__doc__ += '\n    Keyword arguments (* = required):\n'
        wrapper.__doc__ += ''.join(['\t*%s\n' % p for p in required])
        wrapper.__doc__ += ''.join(['\t %s\n' % p for p in optional])

      return wrapper
    return decorator

  @__api_request(optional=['LinodeID'])
  def linode_list(self, request):
    """List information about your Linodes.

    Returns:
        [{u'ALERT_BWIN_ENABLED': 0 or 1,
          u'ALERT_BWIN_THRESHOLD': integer (Mb/sec?),
          u'ALERT_BWOUT_ENABLED': 0 or 1,
          u'ALERT_BWOUT_THRESHOLD': integer (Mb/sec?),
          u'ALERT_BWQUOTA_ENABLED': 0 or 1,
          u'ALERT_BWQUOTA_THRESHOLD': 0..100,
          u'ALERT_CPU_ENABLED': 0 or 1,
          u'ALERT_CPU_THRESHOLD': 0..400 (% CPU),
          u'ALERT_DISKIO_ENABLED': 0 or 1,
          u'ALERT_DISKIO_THRESHOLD': integer (IO ops/sec?),
          u'BACKUPSENABLED': 0 or 1,
          u'BACKUPWEEKLYDAY': 0..6 (day of week; 0 is Sunday),
          u'BACKUPWINDOW': some integer,
          u'DATACENTERID': Datacenter ID,
          u'LABEL': 'linode label',
          u'LINODEID': Linode ID,
          u'LPM_DISPLAYGROUP': 'group label',
          u'STATUS': Status flag,
          u'TOTALHD': available disk (GB),
          u'TOTALRAM': available RAM (MB),
          u'TOTALXFER': available bandwidth (GB/month),
          u'WATCHDOG': 0 or 1}, ...]
    """
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
    """Update information about, or settings for, a Linode.

    See linode_list.__doc__ for information on parameters.

    Returns {u'LinodeID': LinodeID} on successful change.
    """
    pass

  @__api_request(required=['DatacenterID', 'PlanID', 'PaymentTerm'])
  def linode_create(self, request):
    """Create a new Linode.

    WARNING: This will create a billing event.

    Returns {u'LinodeID': LinodeID} on successful creation.
    """
    pass

  @__api_request(required=['LinodeID'])
  def linode_shutdown(self, request):
    """Submit a shutdown job for a Linode.

    Returns {u'JobID': JobID} on successful job submission.
    """
    pass

  @__api_request(required=['LinodeID'], optional=['ConfigID'])
  def linode_boot(self, request):
    """Submit a boot job for a Linode.

    Returns {u'JobID': JobID} on successful job submission.
    """
    pass

  @__api_request(required=['LinodeID'])
  def linode_delete(self, request):
    """Completely, immediately, and totally deletes a Linode.

    WARNING: This will permenantly delete a Linode, running or no.

    Returns {u'LinodeID': LinodeID} on successful destruction.
    """
    pass

  @__api_request(required=['LinodeID'], optional=['ConfigID'])
  def linode_reboot(self, request):
    """Submit a reboot job for a Linode.
    
    Returns {u'JobID': JobID} on successful job submission.
    """
    pass

  @__api_request(required=['LinodeID'])
  def linode_config_list(self, request):
    """Lists all configuration profiles for a given Linode.

    Returns:
        [{u'Comments': 'comments field',
          u'ConfigID': Config ID,
          u'DiskList': ',,,,,,,,' disk array,
          u'helper_depmod': 0 or 1,
          u'helper_disableUpdateDB': 0 or 1,
          u'helper_libtls': 0 or 1,   # maybe
          u'helper_xen': 0 or 1,
          u'KernelID': Kernel ID,
          u'Label': 'Profile name',
          u'LinodeID': Linode ID,
          u'RAMLimit': Max memory (MB), 0 is unlimited,
          u'RootDeviceCustom': '',
          u'RootDeviceNum': root partition (1=first, 0=RootDeviceCustom),
          u'RootDeviceRO': 0 or 1,    # maybe
          u'RunLevel': in ['default', 'single', 'binbash']}, ...]
    """
    pass

  @__api_request(required=['LinodeID', 'ConfigID'], optional=[
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
    """Updates a configuration profile.

    Returns {u'ConfigID': Config ID} on successful update.
    """
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
    """Creates a configuration profile.

    Returns {u'ConfigID': Config ID} on successful creation.
    """
    pass

  @__api_request(required=['LinodeID', 'ConfigID'])
  def linode_config_delete(self, request):
    """Deletes a configuration profile.  This does not delete the Linode
    itself, nor its disk images.

    Returns {u'ConfigID': Config ID} on successful deletion.
    """
    pass
  
  @__api_request(required=['LinodeID'])
  def linode_disk_list(self, request):
    """Lists all disk images associated with a Linode.

    Returns:
        [{u'CREATE_DT': u'YYYY-MM-DD hh:mm:ss.0',
          u'DISKID': Disk ID,
          u'ISREADONLY': 0 or 1,
          u'LABEL': 'Disk label',
          u'LINODEID': Linode ID,
          u'SIZE': Size of disk (MB),
          u'STATUS': Status flag,
          u'TYPE': in ['ext3', 'swap', 'raw'],
          u'UPDATE_DT': u'YYYY-MM-DD hh:mm:ss.0'}, ...]
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID'], optional=['Label', 'isReadOnly'])
  def linode_disk_update(self, request):
    """Updates the information about a disk image.

    Returns {u'DiskID': Disk ID} on successful update.
    """
    pass

  @__api_request(required=['LinodeID', 'Type', 'Size', 'Label'], optional=['isReadOnly'])
  def linode_disk_create(self, request):
    """Submits a job to create a new disk image.

    Returns {u'DiskID': Disk ID, u'JobID': Job ID} on job submission.
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID'])
  def linode_disk_duplicate(self, request):
    """Submits a job to preform a bit-for-bit copy of a disk image.

    Returns {u'DiskID': New Disk ID, u'JobID': Job ID} on job submission.
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID'])
  def linode_disk_delete(self, request):
    """Submits a job to delete a disk image.

    WARNING: All data on the disk image will be lost forever.

    Returns {u'DiskID': Deleted Disk ID, u'JobID': Job ID} on job submission.
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID', 'Size'])
  def linode_disk_resize(self, request):
    """Submits a job to resize a partition.

    Returns {u'DiskID': Disk ID, u'JobID': Job ID} on job submission.
    """
    pass

  @__api_request(required=['LinodeID', 'DistributionID', 'rootPass', 'Label',
                           'Size'], optional=['rootSSHKey'])
  def linode_disk_createfromdistribution(self, request):
    """Submits a job to create a disk image from a Linode template.

    Returns {u'DiskID': New Disk ID, u'JobID': Job ID} on job submission.
    """
    pass

  @__api_request(required=['LinodeID'], optional=['IPAddressID'])
  def linode_ip_list(self, request):
    """Lists a Linode's IP addresses.

    Returns:
        [{u'ISPUBLIC': 0 or 1,
          u'IPADDRESS': '192.168.100.1',
          u'IPADDRESSID': IP address ID,
          u'LINODEID': Linode ID,
          u'RDNS_NAME': 'reverse.dns.name.here'}, ...]
    """
    pass

  @__api_request(required=['LinodeID'], optional=['pendingOnly', 'JobID'])
  def linode_job_list(self, request):
    """Returns the contents of the job queue.

    Returns:
        [{u'ACTION': 'API action' (e.g. u'linode.create'),
          u'DURATION': Duration spent processing or '',
          u'ENTERED_DT': 'yyyy-mm-dd hh:mm:ss.0'
          u'HOST_FINISH_DT': 'yyyy-mm-dd hh:mm:ss.0' or '',
          u'HOST_MESSAGE': 'response from host'
          u'HOST_START_DT': 'yyyy-mm-dd hh:mm:ss.0' or '',
          u'HOST_SUCCESS': 1 or '',
          u'JOBID': Job ID,
          u'LABEL': 'Description of job',
          u'LINODEID': Linode ID}, ...]
    """
    pass

  @__api_request(optional=['isXen'])
  def avail_kernels(self, request):
    """List available kernels.

    Returns:
        [{u'ISXEN': 0 or 1,
          u'KERNELID': Kernel ID,
          u'LABEL': 'kernel version string'}, ...]
    """
    pass

  @__api_request()
  def avail_distributions(self, request):
    """Returns a list of available Linux Distributions.

    Returns:
        [{u'CREATE_DT': 'YYYY-MM-DD hh:mm:ss.0',
          u'DISTRIBUTIONID': Distribution ID,
          u'IS64BIT': 0 or 1,
          u'LABEL': 'Description of image',
          u'MINIMAGESIZE': MB required to deploy image}, ...]
    """
    pass

  @__api_request()
  def avail_datacenters(self, request):
    """Returns a list of Linode data center facilities.

    Returns:
        [{u'DATACENTERID': Datacenter ID,
          u'LOCATION': 'City, ST, USA'}, ...]
    """
    pass

  @__api_request()
  def avail_linodeplans(self, request):
    """Returns a structure of Linode PlanIDs containing PlanIDs, and their
    availability in each datacenter.

    Returns:
        [{u'DISK': Maximum disk allocation (GB),
          u'LABEL': 'Name of plan',
          u'PLANID': Plan ID,
          u'PRICE': Price (US dollars),
          u'RAM': Maximum memory (MB),
          u'XFER': Allowed transfer (GB/mo),
          u'AVAIL': {
             u'Datacenter ID': Quantity, ...}
         }, ...]
    """
    pass

  @__api_request(required=['username', 'password'])
  def user_getapikey(self, request):
    """Given a username and password, returns the user's API key.  The
    key is remembered by this instance for future use.

    Please be advised that this will replace any previous key stored
    by the instance.

    Returns:
        {u'API_KEY': API key string,
         u'USERNAME': Username}
    """
    pass
