"""
A Python shell to interact with the Linode API

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

import api
import simplejson

class ApiInfo:
  valid_commands = {}
  valid_params   = {}

class HighLevel(api.Api):
  def __init__(self, key):
    api.Api.__init__(self, key)
    self.__domain_cache = {}
    self.__domain_cache_valid = False

  @staticmethod
  def valid_commands():
    comms = {}
    for k in api.Api.valid_commands():
      comms[k] = True
    for k in ApiInfo.valid_commands.keys():
      comms[k] = True
    return comms.keys()

  @staticmethod
  def valid_params():
    params = {}
    for k in api.Api.valid_params():
      params[k] = True
    for k in ApiInfo.valid_params.keys():
      params[k] = True
    return params.keys()

  def invalidates_cache(func):
    def wrapper(self, *args, **kw):
      self.__domain_cache_valid = False
      return func(self, *args, **kw)
    wrapper.__name__ = func.__name__
    wrapper.__doc__  = func.__doc__
    wrapper.__dict__.update(func.__dict__)
    return wrapper

  def requires_cache(func):
    def wrapper(self, *args, **kw):
      if not self.__domain_cache_valid:
        self.update_domain_cache()
      return func(self, *args, **kw)
    wrapper.__name__ = func.__name__
    wrapper.__doc__  = func.__doc__
    wrapper.__dict__.update(func.__dict__)
    return wrapper

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

      def wrapper(self, mparams = {}, *__args, **__kw):
        if len(mparams) == 0:
          params = __kw
        else:
          params = mparams

        params = dict([(key.lower(), value) for key,value in params.iteritems()])

        for k in required:
          k = k.lower()
          if not params.has_key(k):
            raise api.MissingRequiredArgument(k)

        return func(self, params)
      wrapper.__name__ = func.__name__
      wrapper.__doc__  = func.__doc__
      wrapper.__dict__.update(func.__dict__)
      return wrapper
    return decorator

  def update_domain_cache(self):
    self.debug('updating domain cache')
    self.__domain_cache_valid = True
    self.__domain_cache_name = {}
    self.__domain_cache_id   = {}
    doms = self.domainList()
    if not self.batching():
      self.batching(True)
      for d in doms:
        self.__domain_cache_name[d['DOMAIN']] = d
        self.__domain_cache_name[d['DOMAIN']]['rr'] = {}
        self.__domain_cache_id[d['DOMAINID']] = d['DOMAIN']
        self.domainResourceList(DomainID=d['DOMAINID'])
      results = self.batchFlush()
      for d in results:
        for rr in d['DATA']:
          self.__domain_cache_name[self.__domain_cache_id[rr['DOMAINID']]]['rr'][rr['NAME']] = rr
      self.batching(False)
  
  @__api_request(['Domain'])
  @requires_cache
  def domainGetByName(self, params):
    """Retrieve a domain by a zone name
    Parameters:
      Domain

    Returns the same as domainGet
    """
    return self.__domain_cache_name[params['domain']]

  @__api_request(['Domain', 'Name'])
  @requires_cache
  def domainResourceGetByName(self, params):
    """Retrieve a resource record by a zone and dns name

    Parameters:
      Domain Name

    Returns the same as domainResourceGet
    """
    return self.__domain_cache_name[params['domain']]['rr'][params['name']]

  @__api_request(['Domain'])
  @requires_cache
  @invalidates_cache
  def domainUpdate(self, params):
    """Update a specific domain

    Parameters:
      Same parameters as domainSave

    If you don't include a
    """
    domain = self.__domain_cache_name[params['domain']]
    for k,v in domain.iteritems():
      if k != 'rr' and not params.has_key(k.lower()):
        params[k] = v
    return api.Api.domainSave(self, params)

  @__api_request(['Domain', 'Name'])
  @requires_cache
  @invalidates_cache
  def domainResourceUpdate(self, params):
    resource = self.__domain_cache_name[params['domain']]['rr'][params['name']]
    for k,v in resource.iteritems():
      if not params.has_key(k.lower()):
        params[k] = v
    return api.Api.domainResourceSave(self, params)

  @invalidates_cache
  def domainSave(self, *args, **kw):
    api.Api.domainSave(self, *args, **kw)
  domainSave.__doc__ = api.Api.domainSave.__doc__

  @invalidates_cache
  def domainResourceSave(self, *args, **kw):
    api.Api.domainResourceSave(self, *args, **kw)
  domainResourceSave.__doc__ = api.Api.domainResourceSave.__doc__

  @invalidates_cache
  def domainDelete(self, *args, **kw):
    api.Api.domainDelete(self, *args, **kw)
  domainDelete.__doc__ = api.Api.domainDelete.__doc__

  @invalidates_cache
  def domainResourceDelete(self, *args, **kw):
    api.Api.domainResourceDelete(self, *args, **kw)
  domainResourceDelete.__doc__ = api.Api.domainResourceDelete.__doc__
