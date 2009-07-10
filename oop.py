from os import environ
from datetime import datetime

from api import Api, LowerCaseDict

_api = Api(environ['LINODE_API_KEY'], debug=True)

class Field(object):
  to_py = lambda self, value: value
  to_linode = to_py

  def __init__(self, field):
    self.field = field

class IntField(Field):
  def to_py(self, value):
    if value is not None:
      return int(value)

  to_linode = to_py

class CharField(Field):
  to_py = lambda self, value: str(value)
  to_linode = to_py

class BoolField(Field):
  def to_py(self, value):
    if value in (1, '1'): return True
    else: return False

  def to_linode(self, value):
    if value: return 1
    else: return 0

class ChoiceField(Field):
  to_py = lambda self, value: value

  def __init__(self, field, choices=[]):
    self.field = field
    self.choices = choices

  def to_linode(self, value):
    if value in self.choices:
      return value
    else:
      raise AttributeError

class ListField(Field):
  to_py = lambda self, value: value.split(',')
  to_linode = lambda self, value: ','.join(value)

class DateTimeField(Field):
  to_py = lambda self, value: datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
  to_linode = lambda self, value: value.strftime('%Y-%m-%d %H:%M:%S')

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
  def list(self, **kw):
    kwargs = {}
    for k, v in kw.items():
      f = self.fields[k.lower()]
      kwargs[f.field] = v
    for l in self.list_method(**kwargs):
      yield self(l)

  @classmethod
  def get(self, **kw):
    kwargs = {}
    for k, v in kw.items():
      f = self.fields[k.lower()]
      kwargs[f.field] = v
    return self(self.list_method(**kwargs)[0])

class Linode(LinodeObject):
  fields = {
    'id'                : IntField('LinodeID'),
    'datacenter'        : IntField('DatacenterID'),
    'plan'              : IntField('PlanID'),
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
    'backup_window'     : Field('backupWindow'),
    'backup_weekly_day' : ChoiceField('backupWeeklyDay', choices=range(6)),
    'watchdog'          : BoolField('watchdog'),
    'total_ram'         : IntField('TotalRam'),
    'total_diskspace'   : IntField('TotalHD'),
    'total_xfer'        : IntField('TotalXfer'),
  }

  update_method = _api.linode_update
  create_method = _api.linode_create
  primary_key   = 'LinodeID'
  list_method   = _api.linode_list

  def boot(self):
    _api.linode_boot(linodeid=self.id)

  def shutdown(self):
    _api.linode_shutdown(linodeid=self.id)

  def reboot(self):
    _api.linode_reboot(linodeid=self.id)

  def delete(self):
    _api.linode_delete(linodeid=self.id)

class LinodeDisk(LinodeObject):
  fields = {
    'id'      : IntField('DiskID'),
    'linode'  : IntField('LinodeID'),
    'type'    : CharField('Type'),
    'size'    : IntField('Size'),
    'name'    : CharField('Label'),
    'label'   : CharField('Label'),
  }

  update_method = _api.linode_disk_update
  create_method = _api.linode_disk_create
  primary_key   = 'DiskID'
  list_method   = _api.linode_disk_list

  def duplicate(self):
    ret = _api.linode_disk_duplicate(linodeid=self.linode, diskid=self.id)
    return LinodeDisk(LinodeDisk.get(linode=self.linode, id=ret['DiskID']))

  def resize(self, size):
    _api.linode_disk_resize(linodeid=self.linode, diskid=self.id, size=size)

  def delete(self):
    _api.linode_disk_delete(linodeid=self.linode, diskid=self.id)

class LinodeConfig(LinodeObject):
  fields = {
    'id'                  : IntField('ConfigID'),
    'linode'              : IntField('LinodeID'),
    'kernel'              : IntField('KernelID'),
    'disklist'            : ListField('DISKLIST'),
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

class Kernel(LinodeObject):
  fields = {
    'id'    : IntField('KernelID'),
    'label' : CharField('Label'),
    'name'  : CharField('Label'),
    'is_xen': BoolField('IsXen'),
  }

  list_method = _api.avail_kernels

class Distribution(LinodeObject):
  fields = {
    'id'        : IntField('DistributionID'),
    'label'     : CharField('Label'),
    'name'      : CharField('Label'),
    'min'       : IntField('MinImageSize'),
    'is_64bit'  : BoolField('Is64Bit'),
    'created'   : DateTimeField('CREATE_DT'),
  }

  list_method = _api.avail_distributions

class Datacenter(LinodeObject):
  fields = {
    'id'        : IntField('DatacenterID'),
    'location'  : CharField('Location'),
    'name'      : CharField('Location'),
  }

  list_method = _api.avail_datacenters

class LinodeJob(LinodeObject):
  fields = {
    'id'            : IntField('LinodeJobID'),
    'linode'        : IntField('LinodeID'),
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

class LinodeIP(LinodeObject):
  fields = {
    'id'        : IntField('IPAddressID'),
    'linode'    : IntField('LinodeID'),
    'address'   : CharField('IPADDRESS'),
    'is_public' : BoolField('ISPUBLIC'),
    'rdns'      : CharField('RDNS_NAME'),
  }

  list_method = _api.linode_ip_list
