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

class FloatField(Field):
  def to_py(self, value):
    if value is not None:
      return float(value)

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

class ForeignField(Field):
  def __init__(self, field):
    self.field = field.primary_key
    self.__model = field

  def to_py(self, value):
    return self.__model.get(id=value)

  def to_linode(self, value):
    if isinstance(value, int):
      return value
    else:
      return value.id
