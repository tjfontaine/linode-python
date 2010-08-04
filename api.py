#!/usr/bin/python
# vim:ts=2:sw=2:expandtab
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
    [{'ERRORCODE': Error code number,
      'ERRORMESSAGE': 'Description of error'}]

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
    41: Linode must have no disks before delete
  """
  
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiInfo:
  valid_commands = {}
  valid_params   = {}

LINODE_API_URL = 'https://api.linode.com/api/'

VERSION = '0.0.1'

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
        api.ApiError: [{'ERRORCODE': 99,
                        'ERRORMESSAGE': 'Error Message'}]

  If you do not specify a key, the only method you may use is
  user_getapikey(username, password).  This will retrieve and store
  the API key for a given user.

  Full documentation on the API can be found from Linode at:
        http://www.linode.com/api/
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
    return list(ApiInfo.valid_commands.keys())

  @staticmethod
  def valid_params():
    """Returns a list of all parameters used by methods of this class."""
    return list(ApiInfo.valid_params.keys())

  def batchFlush(self):
    """Initiates a batch flush.  Raises Exception if not in batching mode."""
    if not self.batching:
      raise Exception('Cannot flush requests when not batching')

    s = json.dumps(self.__batch_cache)
    self.__batch_cache = []
    request = { 'api_action' : 'batch', 'api_requestArray' : s }
    return self.__send_request(request)

  def __getattr__(self, name):
    """Return a callable for any undefined attribute and assume it's an API call"""
    def generic_request(*args, **kw):
      request = LowerCaseDict(kw)
      request['api_action'] = name.replace('_', '.')

      if self.batching:
        self.__batch_cache.append(request)
        logging.debug('Batched: %s', json.dumps(request))
      else:
        return self.__send_request(request)
    generic_request.__name__ = name
    return generic_request

  def __send_request(self, request):
    if self.__key:
      request['api_key'] = self.__key
    elif request['api_action'] != 'user.getapikey':
      raise Exception('Must call user_getapikey to fetch key')

    request['api_responseFormat'] = 'json'

    logging.debug('Parmaters '+str(request))
    request = urllib.urlencode(request)

    headers = {
      'User-Agent': 'LinodePython/'+VERSION,
    }

    req = self.__request(LINODE_API_URL, request, headers)
    response = self.__urlopen(req)
    response = response.read()

    logging.debug('Raw Response: '+response)

    try:
      s = json.loads(response)
    except Exception, ex:
      print(response)
      raise ex

    if isinstance(s, dict):
      s = LowerCaseDict(s)
      if len(s['ERRORARRAY']) > 0:
        if s['ERRORARRAY'][0]['ERRORCODE'] is not 0:
          raise ApiError(s['ERRORARRAY'])
      if s['ACTION'] == 'user.getapikey':
        self.__key = s['DATA']['API_KEY']
        logging.debug('API key is: '+self.__key)
      return s['DATA']
    else:
      return s

  def __api_request(required=[], optional=[], returns=[]):
    """Decorator to define required and optional paramters"""
    for k in required:
      k = k.lower()
      if k not in ApiInfo.valid_params:
        ApiInfo.valid_params[k] = True

    for k in optional:
      k = k.lower()
      if k not in ApiInfo.valid_params:
        ApiInfo.valid_params[k] = True

    def decorator(func):
      if func.__name__ not in ApiInfo.valid_commands:
        ApiInfo.valid_commands[func.__name__] = True

      def wrapper(self, **kw):
        request = LowerCaseDict()
        request['api_action'] = func.__name__.replace('_', '.')

        params = LowerCaseDict(kw)

        for k in required:
          if k not in params:
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
        wrapper.__doc__ += ''.join(['\t *%s\n' % p for p in required])
        wrapper.__doc__ += ''.join(['\t  %s\n' % p for p in optional])

      if returns and wrapper.__doc__:
        # we either have a list of dicts or a just plain dict
        if len(wrapper.__doc__.split('\n')) is 1:  # one-liners need whitespace
          wrapper.__doc__ += '\n' 
        if isinstance(returns, list):
          width = max(len(q) for q in returns[0].keys())
          wrapper.__doc__ += '\n    Returns list of dictionaries:\n\t[{\n'
          wrapper.__doc__ += ''.join(['\t  %-*s: %s\n'
                              % (width, p, returns[0][p]) for p in returns[0].keys()])
          wrapper.__doc__ += '\t }, ...]\n'
        else:
          width = max(len(q) for q in returns.keys())
          wrapper.__doc__ += '\n    Returns dictionary:\n\t {\n'
          wrapper.__doc__ += ''.join(['\t  %-*s: %s\n'
                              % (width, p, returns[p]) for p in returns.keys()])
          wrapper.__doc__ += '\t }\n'

      return wrapper
    return decorator

  @__api_request(optional=['LinodeID'],
                 returns=[{'ALERT_BWIN_ENABLED': '0 or 1',
                           'ALERT_BWIN_THRESHOLD': 'integer (Mb/sec?)',
                           'ALERT_BWOUT_ENABLED': '0 or 1',
                           'ALERT_BWOUT_THRESHOLD': 'integer (Mb/sec?)',
                           'ALERT_BWQUOTA_ENABLED': '0 or 1',
                           'ALERT_BWQUOTA_THRESHOLD': '0..100',
                           'ALERT_CPU_ENABLED': '0 or 1',
                           'ALERT_CPU_THRESHOLD': '0..400 (% CPU)',
                           'ALERT_DISKIO_ENABLED': '0 or 1',
                           'ALERT_DISKIO_THRESHOLD': 'integer (IO ops/sec?)',
                           'BACKUPSENABLED': '0 or 1',
                           'BACKUPWEEKLYDAY': '0..6 (day of week, 0 = Sunday)',
                           'BACKUPWINDOW': 'some integer',
                           'DATACENTERID': 'Datacenter ID',
                           'LABEL': 'linode label',
                           'LINODEID': 'Linode ID',
                           'LPM_DISPLAYGROUP': 'group label',
                           'STATUS': 'Status flag',
                           'TOTALHD': 'available disk (GB)',
                           'TOTALRAM': 'available RAM (MB)',
                           'TOTALXFER': 'available bandwidth (GB/month)',
                           'WATCHDOG': '0 or 1'}])
  def linode_list(self, request):
    """List information about your Linodes.

    Status flag values:
      -2: Boot Failed (not in use)
      -1: Being Created
       0: Brand New
       1: Running
       2: Powered Off
       3: Shutting Down (not in use)
       4: Saved to Disk (not in use)
    """
    pass

  @__api_request(required=['LinodeID'],
                 optional=['Label', 'lpm_displayGroup', 'Alert_cpu_enabled',
                           'Alert_cpu_threshold', 'Alert_diskio_enabled',
                           'Alert_diskio_threshold', 'Alert_bwin_enabled',
                           'Alert_bwin_threshold', 'Alert_bwout_enabled',
                           'Alert_bwout_threshold', 'Alert_bwquota_enabled',
                           'Alert_bwquota_threshold', 'backupWindow',
                           'backupWeeklyDay', 'watchdog'],
                 returns={'LinodeID': 'LinodeID'})
  def linode_update(self, request):
    """Update information about, or settings for, a Linode.

    See linode_list.__doc__ for information on parameters.
    """
    pass

  @__api_request(required=['DatacenterID', 'PlanID', 'PaymentTerm'],
                 returns={'LinodeID': 'New Linode ID'})
  def linode_create(self, request):
    """Create a new Linode.

    This will create a billing event.
    """
    pass

  @__api_request(required=['LinodeID'], returns={'JobID': 'Job ID'})
  def linode_shutdown(self, request):
    """Submit a shutdown job for a Linode.

    On job submission, returns the job ID.  Does not wait for job
    completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID'], optional=['ConfigID'],
                 returns={'JobID': 'Job ID'})
  def linode_boot(self, request):
    """Submit a boot job for a Linode.

    On job submission, returns the job ID.  Does not wait for job
    completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID'], optional=['skipChecks'],
                 returns={'LinodeID': 'Destroyed Linode ID'})
  def linode_delete(self, request):
    """Completely, immediately, and totally deletes a Linode.
    Requires all disk images be deleted first, or that the optional
    skipChecks parameter be set.

    This will create a billing event.

    WARNING: Deleting your last Linode may disable services that
    require a paid account (e.g. DNS hosting).
    """
    pass

  @__api_request(required=['LinodeID'], optional=['ConfigID'],
                 returns={'JobID': 'Job ID'})
  def linode_reboot(self, request):
    """Submit a reboot job for a Linode.
    
    On job submission, returns the job ID.  Does not wait for job
    completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID', 'PlanID'])
  def linode_resize(self, request):
    """Resize a Linode from one plan to another.

    Immediately shuts the Linode down, charges/credits the account, and
    issues a migration to an appropriate host server.
    """
    pass

  @__api_request(required=['LinodeID'],
                 returns=[{'Comments': 'comments field',
                           'ConfigID': 'Config ID',
                           'DiskList': "',,,,,,,,' disk array",
                           'helper_depmod': '0 or 1',
                           'helper_disableUpdateDB': '0 or 1',
                           'helper_libtls': '0 or 1',
                           'helper_xen': '0 or 1',
                           'KernelID': 'Kernel ID',
                           'Label': 'Profile name',
                           'LinodeID': 'Linode ID',
                           'RAMLimit': 'Max memory (MB), 0 is unlimited',
                           'RootDeviceCustom': '',
                           'RootDeviceNum': 'root partition (1=first, 0=RootDeviceCustom)',
                           'RootDeviceRO': '0 or 1',
                           'RunLevel': "in ['default', 'single', 'binbash'"}])
  def linode_config_list(self, request):
    """Lists all configuration profiles for a given Linode."""
    pass

  @__api_request(required=['LinodeID', 'ConfigID'],
                 optional=['KernelID', 'Label', 'Comments', 'RAMLimit',
                           'DiskList', 'RunLevel', 'RootDeviceNum',
                           'RootDeviceCustom', 'RootDeviceRO',
                           'helper_disableUpdateDB', 'helper_xen',
                           'helper_depmod'],
                 returns={'ConfigID': 'Config ID'})
  def linode_config_update(self, request):
    """Updates a configuration profile."""
    pass

  @__api_request(required=['LinodeID', 'KernelID', 'Label', 'Disklist'],
                 optional=['Comments', 'RAMLimit', 'RunLevel',
                           'RootDeviceNum', 'RootDeviceCustom',
                           'RootDeviceRO', 'helper_disableUpdateDB',
                           'helper_xen', 'helper_depmod'],
                 returns={'ConfigID': 'Config ID'})
  def linode_config_create(self, request):
    """Creates a configuration profile."""
    pass

  @__api_request(required=['LinodeID', 'ConfigID'],
                 returns={'ConfigID': 'Config ID'})
  def linode_config_delete(self, request):
    """Deletes a configuration profile.  This does not delete the
    Linode itself, nor its disk images (see linode_disk_delete,
    linode_delete).
    """
    pass
  
  @__api_request(required=['LinodeID'],
                 returns=[{'CREATE_DT': 'YYYY-MM-DD hh:mm:ss.0',
                           'DISKID': 'Disk ID',
                           'ISREADONLY': '0 or 1',
                           'LABEL': 'Disk label',
                           'LINODEID': 'Linode ID',
                           'SIZE': 'Size of disk (MB)',
                           'STATUS': 'Status flag',
                           'TYPE': "in ['ext3', 'swap', 'raw']",
                           'UPDATE_DT': 'YYYY-MM-DD hh:mm:ss.0'}])
  def linode_disk_list(self, request):
    """Lists all disk images associated with a Linode."""
    pass

  @__api_request(required=['LinodeID', 'DiskID'],
                 optional=['Label', 'isReadOnly'],
                 returns={'DiskID': 'Disk ID'})
  def linode_disk_update(self, request):
    """Updates the information about a disk image."""
    pass

  @__api_request(required=['LinodeID', 'Type', 'Size', 'Label'],
                 optional=['isReadOnly'],
                 returns={'DiskID': 'Disk ID', 'JobID': 'Job ID'})
  def linode_disk_create(self, request):
    """Submits a job to create a new disk image.

    On job submission, returns the disk ID and job ID.  Does not
    wait for job completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID'],
                 returns={'DiskID': 'New Disk ID', 'JobID': 'Job ID'})
  def linode_disk_duplicate(self, request):
    """Submits a job to preform a bit-for-bit copy of a disk image.

    On job submission, returns the disk ID and job ID.  Does not
    wait for job completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID'],
                 returns={'DiskID': 'Deleted Disk ID', 'JobID': 'Job ID'})
  def linode_disk_delete(self, request):
    """Submits a job to delete a disk image.

    WARNING: All data on the disk image will be lost forever.

    On job submission, returns the disk ID and job ID.  Does not
    wait for job completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID', 'DiskID', 'Size'],
                 returns={'DiskID': 'Disk ID', 'JobID': 'Job ID'})
  def linode_disk_resize(self, request):
    """Submits a job to resize a partition.

    On job submission, returns the disk ID and job ID.  Does not
    wait for job completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID', 'DistributionID', 'rootPass', 'Label',
                           'Size'],
                 optional=['rootSSHKey'],
                 returns={'DiskID': 'New Disk ID', 'JobID': 'Job ID'})
  def linode_disk_createfromdistribution(self, request):
    """Submits a job to create a disk image from a Linode template.

    On job submission, returns the disk ID and job ID.  Does not
    wait for job completion (see linode_job_list).
    """
    pass

  @__api_request(required=['LinodeID'],
                 returns={'IPAddressID': 'New IP Address ID'})
  def linode_ip_addprivate(self, request):
    """Assigns a Private IP to a Linode.  Returns the IPAddressID
    that was added."""
    pass

  @__api_request(required=['LinodeID'], optional=['IPAddressID'],
                 returns=[{'ISPUBLIC': '0 or 1',
                           'IPADDRESS': '192.168.100.1',
                           'IPADDRESSID': 'IP address ID',
                           'LINODEID': 'Linode ID',
                           'RDNS_NAME': 'reverse.dns.name.here'}])
  def linode_ip_list(self, request):
    """Lists a Linode's IP addresses."""
    pass

  @__api_request(required=['LinodeID'], optional=['pendingOnly', 'JobID'],
                 returns=[{'ACTION': "API action (e.g. 'linode.create')",
                           'DURATION': "Duration spent processing or ''",
                           'ENTERED_DT': 'yyyy-mm-dd hh:mm:ss.0',
                           'HOST_FINISH_DT': "'yyyy-mm-dd hh:mm:ss.0' or ''",
                           'HOST_MESSAGE': 'response from host',
                           'HOST_START_DT': "'yyyy-mm-dd hh:mm:ss.0' or ''",
                           'HOST_SUCCESS': "1 or ''",
                           'JOBID': 'Job ID',
                           'LABEL': 'Description of job',
                           'LINODEID': 'Linode ID'}])
  def linode_job_list(self, request):
    """Returns the contents of the job queue."""
    pass

  @__api_request(optional=['isXen'],
                 returns=[{'ISXEN': '0 or 1',
                           'KERNELID': 'Kernel ID',
                           'LABEL': 'kernel version string'}])
  def avail_kernels(self, request):
    """List available kernels."""
    pass

  @__api_request(returns=[{'CREATE_DT': 'YYYY-MM-DD hh:mm:ss.0',
                           'DISTRIBUTIONID': 'Distribution ID',
                           'IS64BIT': '0 or 1',
                           'LABEL': 'Description of image',
                           'MINIMAGESIZE': 'MB required to deploy image'}])
  def avail_distributions(self, request):
    """Returns a list of available Linux Distributions."""
    pass

  @__api_request(returns=[{'DATACENTERID': 'Datacenter ID',
                           'LOCATION': 'City, ST, USA'}])
  def avail_datacenters(self, request):
    """Returns a list of Linode data center facilities."""
    pass

  @__api_request(returns=[{'DISK': 'Maximum disk allocation (GB)',
                           'LABEL': 'Name of plan', 'PLANID': 'Plan ID',
                           'PRICE': 'Price (US dollars)',
                           'RAM': 'Maximum memory (MB)',
                           'XFER': 'Allowed transfer (GB/mo)',
                           'AVAIL': {'Datacenter ID': 'Quantity'}}])
  def avail_linodeplans(self, request):
    """Returns a structure of Linode PlanIDs containing PlanIDs, and
    their availability in each datacenter.
    """
    pass

  @__api_request(optional=['StackScriptID', 'DistributionID', 'DistributionVendor',
                            'keywords'],
                 returns=[{'CREATE_DT': "'yyyy-mm-dd hh:mm:ss.0'",
                            'DEPLOYMENTSACTIVE': 'The number of Scripts that Depend on this Script',
                            'REV_DT': "'yyyy-mm-dd hh:mm:ss.0'",
                            'DESCRIPTION': 'User defined description of the script',
                            'SCRIPT': 'The actual source of the script',
                            'ISPUBLIC': '0 or 1',
                            'REV_NOTE': 'Comment regarding this revision',
                            'LABEL': 'test',
                            'LATESTREV': 'The number of the latest revision',
                            'DEPLOYMENTSTOTAL': 'Number of times this script has been deployed',
                            'STACKSCRIPTID': 'StackScript ID',
                            'DISTRIBUTIONIDLIST': 'Comma separated list of distributions this script is available'}])
  def avail_stackscripts(self, request):
    """Returns a list of publicly available StackScript.
    """
    pass

  @__api_request(required=['username', 'password'],
                 returns={'API_KEY': 'API key', 'USERNAME': 'Username'})
  def user_getapikey(self, request):
    """Given a username and password, returns the user's API key.  The
    key is remembered by this instance for future use.

    Please be advised that this will replace any previous key stored
    by the instance.
    """
    pass

  @__api_request(optional=['DomainID'],
                 returns=[{'STATUS': 'Status flag',
                           'RETRY_SEC': 'SOA Retry field',
                           'DOMAIN': 'Domain name',
                           'DOMAINID': 'Domain ID number',
                           'DESCRIPTION': 'Description',
                           'MASTER_IPS': 'Master nameservers (for slave zones)',
                           'SOA_EMAIL': 'SOA e-mail address (user@domain)',
                           'REFRESH_SEC': 'SOA Refresh field',
                           'TYPE': 'Type of zone (master or slave)',
                           'EXPIRE_SEC': 'SOA Expire field',
                           'TTL_SEC': 'Default TTL'}])
  def domain_list(self, request):
    """Returns a list of domains associated with this account."""
    pass

  @__api_request(required=['DomainID'],
                 returns={'DomainID': 'Domain ID number'})
  def domain_delete(self, request):
    """Deletes a given domain, by domainid."""
    pass

  @__api_request(required=['Domain', 'Type'],
                 optional=['SOA_Email', 'Refresh_sec', 'Retry_sec',
                           'Expire_sec', 'TTL_sec', 'status', 'master_ips'],
                 returns={'DomainID': 'Domain ID number'})
  def domain_create(self, request):
    """Create a new domain.

    For type='master', SOA_Email is required.
    For type='slave', Master_IPs is required.

    Master_IPs is a comma or semicolon-delimited list of master IPs.
    Status is 1 (Active), 2 (EditMode), or 3 (Off).

    TTL values are rounded up to the nearest valid value:
    300, 3600, 7200, 14400, 28800, 57600, 86400, 172800,
    345600, 604800, 1209600, or 2419200 seconds.
    """
    pass

  @__api_request(required=['DomainID'],
                 optional=['Domain', 'Type', 'SOA_Email', 'Refresh_sec',
                           'Retry_sec', 'Expire_sec', 'TTL_sec', 'status',
                           'master_ips'],
                 returns={'DomainID': 'Domain ID number'})
  def domain_update(self, request):
    """Updates the parameters of a given domain.

    TTL values are rounded up to the nearest valid value:
    300, 3600, 7200, 14400, 28800, 57600, 86400, 172800,
    345600, 604800, 1209600, or 2419200 seconds.
    """
    pass

  @__api_request(required=['DomainID'], optional=['ResourceID'],
                 returns=[{'DOMAINID': 'Domain ID number',
                           'PROTOCOL': 'Protocol (for SRV)',
                           'TTL_SEC': 'TTL for record (0=default)',
                           'WEIGHT': 'Weight (for SRV)',
                           'NAME': 'The hostname or FQDN',
                           'RESOURCEID': 'Resource ID number',
                           'PRIORITY': 'Priority (for MX, SRV)',
                           'TYPE': 'Resource Type (A, MX, etc)',
                           'PORT': 'Port (for SRV)',
                           'TARGET': 'The "right hand side" of the record'}])
  def domain_resource_list(self, request):
    """List the resources associated with a given DomainID."""
    pass

  @__api_request(required=['DomainID', 'Type'],
                 optional=['Name', 'Target', 'Priority', 'Weight',
                           'Port', 'Protocol', 'TTL_Sec'],
                 returns={'ResourceID': 'Resource ID number'})
  def domain_resource_create(self, request):
    """Creates a resource within a given DomainID.

    TTL values are rounded up to the nearest valid value:
    300, 3600, 7200, 14400, 28800, 57600, 86400, 172800,
    345600, 604800, 1209600, or 2419200 seconds.

    For A and AAAA records, specify Target as "[remote_addr]" to
    use the source IP address of the request as the target, e.g.
    for updating pointers to dynamic IP addresses.
    """
    pass

  @__api_request(required=['DomainID', 'ResourceID'],
                 returns={'ResourceID': 'Resource ID number'})
  def domain_resource_delete(self, request):
    """Deletes a Resource from a Domain."""
    pass

  @__api_request(required=['DomainID', 'ResourceID'],
                 optional=['Name', 'Target', 'Priority', 'Weight', 'Port',
                           'Protocol', 'TTL_Sec'],
                 returns={'ResourceID': 'Resource ID number'})
  def domain_resource_update(self, request):
    """Updates a domain resource.

    TTL values are rounded up to the nearest valid value:
    300, 3600, 7200, 14400, 28800, 57600, 86400, 172800,
    345600, 604800, 1209600, or 2419200 seconds.

    For A and AAAA records, specify Target as "[remote_addr]" to
    use the source IP address of the request as the target, e.g.
    for updating pointers to dynamic IP addresses.
    """
    pass

  @__api_request(optional=['StackScriptID'],
                 returns=[{'CREATE_DT': "'yyyy-mm-dd hh:mm:ss.0'",
                            'DEPLOYMENTSACTIVE': 'The number of Scripts that Depend on this Script',
                            'REV_DT': "'yyyy-mm-dd hh:mm:ss.0'",
                            'DESCRIPTION': 'User defined description of the script',
                            'SCRIPT': 'The actual source of the script',
                            'ISPUBLIC': '0 or 1',
                            'REV_NOTE': 'Comment regarding this revision',
                            'LABEL': 'test',
                            'LATESTREV': 'The number of the latest revision',
                            'DEPLOYMENTSTOTAL': 'Number of times this script has been deployed',
                            'STACKSCRIPTID': 'StackScript ID',
                            'DISTRIBUTIONIDLIST': 'Comma separated list of distributions this script is available'}])
  def stackscript_list(self, request):
    """List StackScripts you have created.
    """
    pass

  @__api_request(required=['Label', 'DistributionIDList', 'script'],
                 optional=['Description', 'isPublic', 'rev_note'],
                 returns={'STACKSCRIPTID' : 'ID of the created StackScript'})
  def stackscript_create(self, request):
    """Create a StackScript
    """
    pass

  @__api_request(required=['StackScriptID'],
                 optional=['Label', 'Description', 'DistributionIDList',
                           'isPublic', 'rev_note', 'script'])
  def stackscript_update(self, request):
    """Update an existing StackScript
    """
    pass

  @__api_request(required=['StackScriptID'])
  def stackscript_delete(self, request):
    """Delete an existing StackScript
    """
    pass

