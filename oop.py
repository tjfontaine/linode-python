from os import environ

from api import Api

_api = Api(environ['LINODE_API_KEY'], debug=True)

def bool(value):
  if value in (1, '1'):
    return True
  else:
    return False

def unbool(value):
  if value:
    return 1
  else:
    return 0

class Linode(object):
  fields = {
    'id'                : ('LinodeID', int, None),
    'name'              : ('Label', str, None),
    'label'             : ('Label', str, None),
    'group'             : ('lpm_displayGroup', None, None),
    'cpu_enabled'       : ('Alert_cpu_enabled', bool, unbool),
    'cpu_threshold'     : ('Alert_cpu_threshold', int, None),
    'diskio_enabled'    : ('Alert_diskio_enabled', bool, unbool),
    'diskio_threshold'  : ('Alert_diskio_enabled', int, None),
    'bwin_enabled'      : ('Alert_bwin_enabled', bool, unbool),
    'bwin_threshold'    : ('Alert_bwin_threshold', int, None),
    'bwout_enabled'     : ('Alert_bwout_enabeld', bool, unbool),
    'bwout_threshold'   : ('Alert_bwout_threshold', int, None),
    'bwquota_enabled'   : ('Alert_bwquota_enabled', bool, unbool),
    'bwquota_threshold' : ('Alert_bwquota_threshold', int, None),
    'backup_window'     : ('backupWindow', None, None),
    'backup_weekly_day' : ('backupWeeklyDay', None, None),
    'watchdog'          : ('watchdog', bool, unbool),
  }

  def __init__(self, entry={}):
    self.__entry = dict([(str(k).lower(),v) for k,v in entry.items()])

  def __getattr__(self, name):
    name = name.replace('_Linode', '')
    if name == '__entry':
      return self.__dict__[name]
    elif not self.fields.has_key(name):
      raise AttributeError
    else:
      field, conversion, deconvert = self.fields[name]
      value = None
      if self.__entry.has_key(field.lower()):
        value = self.__entry[field.lower()]
        if conversion:
          value = conversion(value)
      return value

  def __setattr__(self, name, value):
    name = name.replace('_Linode', '').lower()
    if name == '__entry':
      object.__setattr__(self, name, value)
    elif not self.fields.has_key(name):
      raise AttributeError
    else:
      field, conversion, deconvert = self.fields[name]
      if deconvert:
        value = deconvert(value)
      elif conversion:
        value = conversion(value)
      self.__entry[field.lower()] = value

  def save(self):
    if self.id:
      self.update()
    else:
      _api.linode_create(**self.__entry)

  def update(self):
    _api.linode_update(**self.__entry)

  def boot(self):
    _api.linode_boot(linodeid=self.id)

  def shutdown(self):
    _api.linode_shutdown(linodeid=self.id)

  def reboot(self):
    _api.linode_reboot(linodeid=self.id)

  def delete(self):
    _api.linode_delete(linodeid=self.id)

  @staticmethod
  def list():
    for l in _api.linode_list():
      yield Linode(l)

  @staticmethod
  def get(id):
    return Linode(_api.linode_list(linodeid=id)[0])
