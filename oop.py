from os import environ
from datetime import datetime

from api import Api, LowerCaseDict
from fields import *

_api = Api(environ['LINODE_API_KEY'], debug=True)

_id_cache = {}

class LinodeObject(object):
  fields = None
  update_method = None
  create_method = None
  primary_key   = None
  list_method   = None

  def __init__(self, entry={}):
    self.__entry = LowerCaseDict(entry)

  def __getattr__(self, name):
    name = name.replace('_LinodeObject', '')
    if name == '__entry':
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
    if name == '__entry':
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
        s.append('%s: %s' % (k, str(v.to_py(self.__entry[v.field]))))
    return '['+', '.join(s)+']'

  def save(self):
    if self.id:
      self.update()
    else:
      self.id = self.create_method(**self.__entry)[self.primary_key]

  def update(self):
    self.update_method(**self.__entry)

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

    for l in self.list_method(**kwargs):
      l = LowerCaseDict(l)
      _id_cache[self][l[self.primary_key]] = l
      yield self(l)

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

    if not result:
      result = LowerCaseDict(self.list_method(**kwargs)[0])
      _id_cache[self][result[self.primary_key]] = result

    return self(result)

  def cache_remove(self):
    del _id_cache[self.__class__][self.__entry[self.primary_key]]

class Datacenter(LinodeObject):
  fields = {
    'id'        : IntField('DatacenterID'),
    'location'  : CharField('Location'),
    'name'      : CharField('Location'),
  }

  list_method = _api.avail_datacenters
  primary_key =  'DatacenterID'

class LinodePlan(LinodeObject):
  fields = {
    'id'      : IntField('PlanID'),
    'label'   : CharField('Label'),
    'price'   : FloatField('Price'),
    'ram'     : IntField('Ram'),
    'xfer'    : IntField('Xfer'),
  }

  list_method = _api.avail_linodeplans
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

  update_method = _api.linode_update
  create_method = _api.linode_create
  primary_key   = 'LinodeID'
  list_method   = _api.linode_list

  def boot(self):
    ### TODO XXX FIXME return LinodeJob
    return _api.linode_boot(linodeid=self.id)['JobID']

  def shutdown(self):
    ### TODO XXX FIXME return LinodeJob
    return _api.linode_shutdown(linodeid=self.id)['JobID']

  def reboot(self):
    ### TODO XXX FIXME return LinodeJob
    return _api.linode_reboot(linodeid=self.id)['JobID']

  def delete(self):
    _api.linode_delete(linodeid=self.id)
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

  list_method = _api.linode_job_list
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

  list_method = _api.avail_distributions
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

  update_method = _api.linode_disk_update
  create_method = _api.linode_disk_create
  primary_key   = 'DiskID'
  list_method   = _api.linode_disk_list

  def duplicate(self):
    ret = _api.linode_disk_duplicate(linodeid=self.linode.id, diskid=self.id)
    disk = LinodeDisk.get(linode=self.linode, id=ret['DiskID'])
    job = LinodeJob(linode=self.linode, id=ret['JobID'])
    return (disk, job)

  def resize(self, size):
    ret = _api.linode_disk_resize(linodeid=self.linode.id, diskid=self.id, size=size)
    return LinodeJob.get(linode=self.linode, id=ret['JobID'])

  def delete(self):
    ret = _api.linode_disk_delete(linodeid=self.linode.id, diskid=self.id)
    job = LinodeJob.get(linode=self.linode, id=ret['JobID'])
    self.cache_remove()
    return job

  @classmethod
  def create_from_distribution(self, linode, distribution, root_pass, label, size, ssh_key=None):
    l = ForeignField(Linode).to_linode(linode)
    d = ForeignField(Distribution).to_linode(distribution)
    ret = _api.linode_disk_createfromdistribution(linodeid=l, distributionid=d,
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

  list_method = _api.avail_kernels
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

  update_method = _api.linode_config_update
  create_method = _api.linode_config_create
  primary_key   = 'ConfigID'
  list_method   = _api.linode_config_list

  def delete(self):
    self.cache_remove()
    _api.linode_config_delete(linodeid=self.linode.id, configid=self.id)

class LinodeIP(LinodeObject):
  fields = {
    'id'        : IntField('IPAddressID'),
    'linode'    : ForeignField(Linode),
    'address'   : CharField('IPADDRESS'),
    'is_public' : BoolField('ISPUBLIC'),
    'rdns'      : CharField('RDNS_NAME'),
  }

  list_method = _api.linode_ip_list

def fill_cache():
  #_api.batching(True)
  a = [i for i in Linode.list()]
  a = [i for i in Datacenter.list()]
  a = [i for i in LinodePlan.list()]
  a = [i for i in Kernel.list()]
  #_api.batchFlush()
  #_api.batching(False)
