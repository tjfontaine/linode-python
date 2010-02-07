import logging

from os import environ

from api import Api, LowerCaseDict
from fields import *

_api = Api('')

_id_cache = {}

apikey = ''

class LinodeObject(object):
  fields = None
  update_method = None
  create_method = None
  primary_key   = None
  list_method   = None

  def __init__(self, entry={}):
    entry = dict([(str(k), v) for k,v in entry.items()])
    self.__entry = LowerCaseDict(entry)
    self.__api = Api(apikey)

  def __getattr__(self, name):
    name = name.replace('_LinodeObject', '')
    if name in ('__entry', '__api'):
      return self.__dict__[name]
    elif not self.fields.has_key(name):
      raise AttributeError
    else:
      f= self.fields[name]
      value = None
      if self.__entry.has_key(f.field.lower()):
        value = self.__entry[f.field.lower()]
      return f.to_py(value)

  def __setattr__(self, name, value):
    name = name.replace('_LinodeObject', '')
    if name in ('__entry', '__api'):
      object.__setattr__(self, name, value)
    elif not self.fields.has_key(name):
      raise AttributeError
    else:
      f = self.fields[name]
      self.__entry[f.field.lower()] = f.to_linode(value)

  def __str__(self):
    s = []
    for k,v in self.fields.items():
      if self.__entry.has_key(v.field):
        value = v.to_py(self.__entry[v.field])
        if isinstance(value, list):
          s.append('%s: [%s]' % (k, ', '.join([str(x) for x in value])))
        else:
          s.append('%s: %s' % (k, str(value)))
    return '['+', '.join(s)+']'

  def save(self):
    if self.id:
      self.update()
    else:
      self.id = self.create_method(self.__api, **self.__entry)[self.primary_key]

  def update(self):
    self.update_method(self.__api, **self.__entry)

  @classmethod
  def __resolve_kwargs(self, kw):
    kwargs = {}
    for k, v in kw.items():
      f = self.fields[k.lower()]
      kwargs[f.field] = f.to_linode(v)
    return kwargs

  @classmethod
  def list(self, **kw):
    kwargs = self.__resolve_kwargs(kw)

    if not _id_cache.has_key(self):
      _id_cache[self] = {}

    try:
      a = self.__api
    except AttributeError:
      self.__api = Api(apikey)

    for l in self.list_method(self.__api, **kwargs):
      l = LowerCaseDict(l)
      o = self(l)
      o.cache_add()
      yield o

  @classmethod
  def get(self, **kw):
    kwargs = self.__resolve_kwargs(kw)

    if not _id_cache.has_key(self):
      _id_cache[self] = {}

    result = None
    for k,v in _id_cache[self].items():
      found = True
      for i, j in kwargs.items():
        if not v.has_key(i) or v[i] != j:
          found = False
          break
      if not found:
        continue
      else:
        result = v
        break

    try:
      a = self.__api
    except AttributeError:
      self.__api = Api(apikey)

    if not result:
      result = LowerCaseDict(self.list_method(self.__api, **kwargs)[0])
      o = self(result)
      o.cache_add()
      return o
    else:
      return self(result)

  def cache_remove(self):
    del _id_cache[self.__class__][self.__entry[self.primary_key]]

  def cache_add(self):
    key = self.__class__
    if not _id_cache.has_key(key):
      _id_cache[key] = {}

    _id_cache[key][self.__entry[self.primary_key]] = self.__entry

class Datacenter(LinodeObject):
  fields = {
    'id'        : IntField('DatacenterID'),
    'location'  : CharField('Location'),
    'name'      : CharField('Location'),
  }

  list_method = Api.avail_datacenters
  primary_key =  'DatacenterID'

class LinodePlan(LinodeObject):
  fields = {
    'id'      : IntField('PlanID'),
    'label'   : CharField('Label'),
    'price'   : FloatField('Price'),
    'ram'     : IntField('Ram'),
    'xfer'    : IntField('Xfer'),
  }

  list_method = Api.avail_linodeplans
  primary_key = 'PlanID'

class Linode(LinodeObject):
  fields = {
    'id'                : IntField('LinodeID'),
    'datacenter'        : ForeignField(Datacenter),
    'plan'              : ForeignField(LinodePlan),
    'term'              : ChoiceField('PaymentTerm', choices=[1, 12, 24]),
    'name'              : CharField('Label'),
    'label'             : CharField('Label'),
    'group'             : Field('lpm_displayGroup'),
    'cpu_enabled'       : BoolField('Alert_cpu_enabled'),
    'cpu_threshold'     : IntField('Alert_cpu_threshold'),
    'diskio_enabled'    : BoolField('Alert_diskio_enabled'),
    'diskio_threshold'  : IntField('Alert_diskio_enabled'),
    'bwin_enabled'      : BoolField('Alert_bwin_enabled'),
    'bwin_threshold'    : IntField('Alert_bwin_threshold'),
    'bwout_enabled'     : BoolField('Alert_bwout_enabeld'),
    'bwout_threshold'   : IntField('Alert_bwout_threshold'),
    'bwquota_enabled'   : BoolField('Alert_bwquota_enabled'),
    'bwquota_threshold' : IntField('Alert_bwquota_threshold'),
    'backup_window'     : IntField('backupWindow'),
    'backup_weekly_day' : ChoiceField('backupWeeklyDay', choices=range(6)),
    'watchdog'          : BoolField('watchdog'),
    'total_ram'         : IntField('TotalRam'),
    'total_diskspace'   : IntField('TotalHD'),
    'total_xfer'        : IntField('TotalXfer'),
    'status'            : IntField('Status'),
  }

  update_method = Api.linode_update
  create_method = Api.linode_create
  primary_key   = 'LinodeID'
  list_method   = Api.linode_list

  def boot(self):
    ### TODO XXX FIXME return LinodeJob
    return self.__api.linode_boot(linodeid=self.id)['JobID']

  def shutdown(self):
    ### TODO XXX FIXME return LinodeJob
    return self.__api.linode_shutdown(linodeid=self.id)['JobID']

  def reboot(self):
    ### TODO XXX FIXME return LinodeJob
    return self.__api.linode_reboot(linodeid=self.id)['JobID']

  def delete(self):
    self.__api.linode_delete(linodeid=self.id)
    self.cache_remove()

class LinodeJob(LinodeObject):
  fields = {
    'id'            : IntField('JobID'),
    'linode'        : ForeignField(Linode),
    'label'         : CharField('Label'),
    'name'          : CharField('Label'),
    'entered'       : DateTimeField('ENTERED_DT'),
    'started'       : DateTimeField('HOST_START_DT'),
    'finished'      : DateTimeField('HOST_FINISH_DT'),
    'message'       : CharField('HOST_MESSAGE'),
    'duration'      : IntField('DURATION'),
    'success'       : BoolField('HOST_SUCCESS'),
    'pending_only'  : BoolField('PendingOnly'),
  }

  list_method = Api.linode_job_list
  primary_key = 'JobID'

class Distribution(LinodeObject):
  fields = {
    'id'        : IntField('DistributionID'),
    'label'     : CharField('Label'),
    'name'      : CharField('Label'),
    'min'       : IntField('MinImageSize'),
    '64bit'     : BoolField('Is64Bit'),
    'created'   : DateTimeField('CREATE_DT'),
  }

  list_method = Api.avail_distributions
  primary_key = 'DistributionID'

class LinodeDisk(LinodeObject):
  fields = {
    'id'      : IntField('DiskID'),
    'linode'  : ForeignField(Linode),
    'type'    : ChoiceField('Type', choices=['ext3', 'swap', 'raw']),
    'size'    : IntField('Size'),
    'name'    : CharField('Label'),
    'label'   : CharField('Label'),
    'status'  : IntField('Status'),
    'created' : DateTimeField('Create_DT'),
    'updated' : DateTimeField('Update_DT'),
    'readonly': BoolField('IsReadonly'),
  }

  update_method = Api.linode_disk_update
  create_method = Api.linode_disk_create
  primary_key   = 'DiskID'
  list_method   = Api.linode_disk_list

  def duplicate(self):
    ret = Api.linode_disk_duplicate(linodeid=self.linode.id, diskid=self.id)
    disk = LinodeDisk.get(linode=self.linode, id=ret['DiskID'])
    job = LinodeJob(linode=self.linode, id=ret['JobID'])
    return (disk, job)

  def resize(self, size):
    ret = Api.linode_disk_resize(linodeid=self.linode.id, diskid=self.id, size=size)
    return LinodeJob.get(linode=self.linode, id=ret['JobID'])

  def delete(self):
    ret = Api.linode_disk_delete(linodeid=self.linode.id, diskid=self.id)
    job = LinodeJob.get(linode=self.linode, id=ret['JobID'])
    self.cache_remove()
    return job

  @classmethod
  def create_from_distribution(self, linode, distribution, root_pass, label, size, ssh_key=None):
    l = ForeignField(Linode).to_linode(linode)
    d = ForeignField(Distribution).to_linode(distribution)
    ret = Api.linode_disk_createfromdistribution(linodeid=l, distributionid=d,
            rootpass=root_pass, label=label, size=size, rootsshkey=ssh_key)
    disk = self.get(id=ret['DiskID'], linode=linode)
    job = LinodeJob(id=ret['JobID'], linode=linode)
    return (disk, job)

class Kernel(LinodeObject):
  fields = {
    'id'    : IntField('KernelID'),
    'label' : CharField('Label'),
    'name'  : CharField('Label'),
    'is_xen': BoolField('IsXen'),
  }

  list_method = Api.avail_kernels
  primary_key = 'KernelID'

class LinodeConfig(LinodeObject):
  fields = {
    'id'                  : IntField('ConfigID'),
    'linode'              : ForeignField(Linode),
    'kernel'              : ForeignField(Kernel),
    'disklist'            : ListField('DiskList', type=ForeignField(LinodeDisk)),
    'name'                : CharField('Label'),
    'label'               : CharField('Label'),
    'comments'            : CharField('Comments'),
    'ram_limit'           : IntField('RAMLimit'),
    'root_device_num'     : IntField('RootDeviceNum'),
    'root_device_custom'  : IntField('RootDeviceCustom'),
    'root_device_readonly': BoolField('RootDeviceRO'),
    'disable_updatedb'    : BoolField('helper_disableUpdateDB'),
    'helper_xen'          : BoolField('helper_xen'),
    'helper_depmod'       : BoolField('helper_depmod'),
  }

  update_method = Api.linode_config_update
  create_method = Api.linode_config_create
  primary_key   = 'ConfigID'
  list_method   = Api.linode_config_list

  def delete(self):
    self.cache_remove()
    self.__api.linode_config_delete(linodeid=self.linode.id, configid=self.id)

class LinodeIP(LinodeObject):
  fields = {
    'id'        : IntField('IPAddressID'),
    'linode'    : ForeignField(Linode),
    'address'   : CharField('IPADDRESS'),
    'is_public' : BoolField('ISPUBLIC'),
    'rdns'      : CharField('RDNS_NAME'),
  }

  list_method = Api.linode_ip_list
  primary_key = 'IPAddressID'

class Domain(LinodeObject):
  fields = {
    'id'        : IntField('DomainID'),
    'domain'    : CharField('Domain'),
    'name'      : CharField('Domain'),
    'type'      : ChoiceField('Type', choices=['master', 'slave']),
    'soa_email' : CharField('SOA_Email'),
    'refresh'   : IntField('Refresh_sec'),
    'retry'     : IntField('Retry_sec'),
    'expire'    : IntField('Expire_sec'),
    'ttl'       : IntField('TTL_sec'),
    'status'    : ChoiceField('Status', choices=[1, 2, 3]),
    'master_ips': ListField('master_ips', type=CharField('master_ips')),
  }

  update_method = Api.domain_update
  create_method = Api.domain_create
  primary_key   = 'DomainID'
  list_method   = Api.domain_list

  STATUS_ON   = 1
  STATUS_EDIT = 2
  STATUS_OFF  = 3

  def delete(self):
    self.cache_remove()
    self.__api.domain_delete(domainid=self.id)

class Resource(LinodeObject):
  fields = {
    'id'        : IntField('ResourceID'),
    'domain'    : ForeignField(Domain),
    'name'      : CharField('Name'),
    'type'      : CharField('Type'),
    'target'    : CharField('Target'),
    'priority'  : IntField('Priority'),
    'weight'    : IntField('Weight'),
    'port'      : IntField('Port'),
    'protocol'  : CharField('Protocol'),
    'ttl'       : IntField('TTL_sec'),
  }

  update_method = Api.domain_resource_update
  create_method = Api.domain_resource_create
  primary_key   = 'ResourceID'
  list_method   = Api.domain_resource_list

  def delete(self):
    self.cache_remove()
    Api.domain_resource_delete(domainid=self.domain.id, resourceid=self.id)

def _iter_class(self, results):
  _id_cache[self] = {}
  results = LowerCaseDict(results)

  d = results['data']
  for i in d: self(i).cache_add()

def fill_cache():
  _api.batching = True
  _api.linode_list()
  _api.avail_linodeplans()
  _api.avail_datacenters()
  _api.avail_distributions()
  _api.avail_kernels()
  _api.domain_list()
  ret = _api.batchFlush()

  for i,k in enumerate([Linode, LinodePlan, Datacenter, Distribution, Kernel, Domain]):
    _iter_class(k, ret[i])

  for k in _id_cache[Linode].keys():
    _api.linode_config_list(linodeid=k)
    _api.linode_disk_list(linodeid=k)

  for k in _id_cache[Domain].keys():
    _api.domain_resource_list(domainid=k)

  ret = _api.batchFlush()

  for r in ret:
    r = LowerCaseDict(r)
    if r['action'] == 'linode.config.list':
      _iter_class(LinodeConfig, r)
    elif r['action'] == 'linode.disk.list':
      _iter_class(LinodeDisk, r)
    elif r['action'] == 'domain.resource.list':
      _iter_class(Resource, r)

  _api.batching = False

def setup_logging():
  logging.basicConfig(level=logging.DEBUG)
