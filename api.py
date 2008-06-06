#!/usr/bin/python
"""
Copyright (c) 2008 Timothy J Fontaine <tjfontaine@gmail.com>

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
  """\
  Exception raised when a required parameter is missing.
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class ApiError(Exception):
  """\
  Exception raised when the Linode API returns an error.
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class Api:
  def __init__(self, key):
    self.__key = key
    self.__url = 'http://beta.linode.com/api/'
    self.__urlopen = urllib2.urlopen
    self.__request = urllib2.Request

  def __send_request(self, request):
    request['api_key'] = self.__key
    request['resultFormat'] = 'json'
    request = urllib.urlencode(request)
    req = self.__request(self.__url,request)
    response = self.__urlopen(req)
    response = response.read()
    json = simplejson.loads(response)
    if len(json['ERRORARRAY']) > 0:
      raise ApiError(json['ERRORARRAY'])
    return json['DATA']

  def __simple_decorator(decorator):
    def new_decorator(f):
      g = decorator(f)
      g.__name__ = f.__name__
      g.__doc__ = f.__doc__
      g.__dict__.update(f.__dict__)
      return g
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator

  @__simple_decorator
  def __api_request(func):
    def decorator(self, *__args, **__kw):
      request = {'action' : func.__name__}
      for k in __kw: request[k] = __kw[k]
      if len(__args) == 1:
        for k in __args[0]: request[k] = __args[0][k]
      result = func(self, request)
      if result is not None:
        request = result
      return self.__send_request(request)
    return decorator

  @__simple_decorator
  def __api_required(*args, **kw):
    def decorator(func):
      def wrapper(*__args,**__kw):
        for k in args:
          if not __kw.has_key(k) and (len(__args) == 2 and not __args[1].has_key(k)):
            raise MissingRequiredArgument(k)
        return func(*__args,**__kw)
      wrapper.__name__ = func.__name__
      wrapper.__doc__ = func.__doc__
      wrapper.__dict__.update(func.__dict__)
      return wrapper
    return decorator

  @__api_request
  def domainList(self, request):
    """\
    List the domains (zones) visible to the user.
    Parameters:
      None
    Retruned fields:
      DOMAINID       - The unique ID for this zone
      DOMAIN         - The zone's name e.g. 'linode.com'
      TYPE           - The zone type: 'master' or 'slave'
      STATUS         - The zone's current status (see below)
      SOA_EMAIL      - SOA email address for the zone
      REFRESH_SEC *  - 'refresh' value for the zone
      RETRY_SEC *    - 'retry' value for the zone
      TTL_SEC *      - 'ttl' value for the zone
    Possible values for STATUS
      0 - Disabled   - The zone is not being served
      1 - Active     - The zone is being served
      2 - Edit Mode  - The zone is being served but changes are not rendered
      3 - Has Errors - The zone has errors in the rendered zonefile
    
    * A value of zero indicates the default time
    """

  @__api_required('DomainID')
  @__api_request
  def domainGet(self, request):
    """\
    Retreive the details for a specific domain.
    Parameters:
      DomainID       - The unique ID for the zone requested (required)
    Retruned fields:
      DOMAINID       - The unique ID for this zone
      DOMAIN         - The zone's name e.g. 'linode.com'
      TYPE           - The zone type: 'master' or 'slave'
      STATUS         - The zone's status (see below)
      SOA_EMAIL      - SOA email address for the zone
      REFRESH_SEC *  - 'refresh' value for the zone
      RETRY_SEC *    - 'retry' value for the zone
      TTL_SEC *      - 'ttl' value for the zone
    Possible values for STATUS
      0 - Disabled   - The zone is not being served
      1 - Active     - The zone is being served
      2 - Edit Mode  - The zone is being served but changes are not rendered
      3 - Has Errors - The zone has errors in the rendered zonefile
    """

  @__api_required('DomainID', 'Domain', 'Type', 'Status', 'SOA_Email')
  @__api_request
  def domainSave(self, request):
    """\
    Create or update a domain within the DNS manger.
    Parameters:
      None
    Retruned fields:
      DOMAINID       - The unique ID for this zone
    Possible values for STATUS
      0 - Disabled   - The zone is not being served
      1 - Active     - The zone is being served
      2 - Edit Mode  - The zone is being served but changes are not rendered
      3 - Has Errors - The zone has errors in the rendered zonefile
    """

  @__api_required('DomainID')
  @__api_request
  def domainResourceList(self, request):
    """\
    List the resource records associated with a particular domain.
    Parameters:
      None
    Retruned fields:
      DOMAINID       - The unique ID for this zone
    """

  @__api_required('ResourceID')
  @__api_request
  def domainResourceGet(self, request):
    """\
    Retrieve the details for a specific resource record.
    Parameters:
      None
    Retruned fields:
      DOMAINID       - The unique ID for this zone
    """

  @__api_required('ResourceID', 'DomainID')
  @__api_request
  def domainResourceSave(self, request):
    """\
    Create or update a resource record.
    Parameters:
      None
    Retruned fields:
      DOMAINID       - The unique ID for this zone
    """

  @__api_request
  def linodeList(self, request):
    """\
    Lists the Lindodes visible to the user.
    Parameters:
      None
    Retruned fields:
      LINODEID       - The unique ID for this Linode
      STATUS         - The Linode's status (see below)
      HOSTHOSTNAME   - The DNS name for the host the Linode is on
      LISHUSERNAME   - The username to connect to a Lish session
      LABEL          - The label for the Linode, as seen on the Linode Manager
      TOTALRAM       - Total RAM assigned to this Linode (MiB)
      TOTALHD        - Total hard drive space assigned to this Linode (MiB)
      TOTALXFER      - Total transfer assigned to this Linode (GiB)
    Possible values for STATUS
      0 - Disabled   - The zone is not being served
      1 - Active     - The zone is being served
      2 - Edit Mode  - The zone is being served but changes are not rendered
      3 - Has Errors - The zone has errors in the rendered zonefile
    """

if __name__ == "__main__":
  from getpass import getpass
  import readline
  import atexit
  import os

  valid_commands = []
  for c in dir(Api):
    if c[0] != '_':
      valid_commands.append(c)

  valid_commands.append('help')
  valid_commands.append('exit')

  def complete(text, state):
    results = [x for x in valid_commands if x.startswith(text)] + [None]
    return results[state]

  readline.set_completer(complete)
  readline.parse_and_bind("tab: complete")
  
  histfile = os.path.expanduser('~/.linode-console-history')
  if hasattr(readline, "read_history_file"):
    try:
      readline.read_history_file(histfile)
    except IOError:
      pass
      atexit.register(readline.write_history_file, histfile)

  key = getpass('Enter API Key: ')
  lapi = Api(key)
  quitting = False
  
  while not quitting:
    command = raw_input('> ')
    if command.lower() == 'exit':
      quitting = True
    elif command.lower() == 'help':
      print ' '.join(valid_commands)
    elif hasattr(lapi, command):
      params = raw_input('Enter named parameters (name:param[,name2:param2]): ')
      method = getattr(lapi, command)
      keywords = {}
      if params != '':
        for p in params.split(','):
          a = p.split(':')
          keywords[a[0]] = a[1]
      ret = method(keywords)
      print simplejson.dumps(ret, indent=2)
