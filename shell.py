#!/usr/bin/python
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
import code
import rlcompleter
import readline
import atexit
import os

class LinodeConsole(code.InteractiveConsole):
  def __init__(self, locals=None, filename="<console>",
      histfile=os.path.expanduser("~/.linode-console-history")):
    code.InteractiveConsole.__init__(self)
    self.init_history(histfile)
    
  def init_history(self, histfile):
    if hasattr(readline, "read_history_file"):
      try:
        readline.read_history_file(histfile)
      except IOError:
        pass
        atexit.register(self.save_history, histfile)

  def save_history(self, histfile):
    readline.write_history_file(histfile)

class LinodeComplete(rlcompleter.Completer):
  def complete(self, text, state):
    result = rlcompleter.Completer.complete(self, text, state)
    if result and result.find('_') > -1:
      result = ''
    return result


if __name__ == "__main__":
  from getpass import getpass
  from os import environ

  if environ.has_key('LINODE_API_KEY'):
    key = environ['LINODE_API_KEY']
  else:
    key = getpass('Enter API Key: ')
  linode = api.Api(key)
  console = LinodeConsole()

  console.runcode('import readline,rlcompleter,api,shell,simplejson')
  console.runcode('readline.parse_and_bind("tab: complete")')
  console.runcode('readline.set_completer(shell.LinodeComplete().complete)')
  console.runcode('def pp(text=None): print simplejson.dumps(text, indent=2)')
  console.locals.update({'linode':linode})
  console.interact()
