#!/usr/bin/env python
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
    if result and result.find('__') > -1:
      result = ''
    return result


if __name__ == "__main__":
  from getpass import getpass
  from os import environ
  import getopt, sys
  try:
    import json
  except:
    import simplejson as json

  if 'LINODE_API_KEY' in environ:
    key = environ['LINODE_API_KEY']
  else:
    key = getpass('Enter API Key: ')

  linode = api.Api(key)

  def usage(all=False):
    print('shell.py --<api action> [--parameter1=value [--parameter2=value [...]]]')
    print('Valid Actions')
    for a in sorted(linode.valid_commands()):
      print('\t--'+a)
    if all:
      print('Valid Named Parameters')
      for a in sorted(linode.valid_params()):
        print('\t--'+a+'=')
    else:
      print('To see valid parameters use: --help --all')

  options = []
  for arg in linode.valid_params():
    options.append(arg+'=')

  for arg in linode.valid_commands():
    options.append(arg)
  options.append('help')
  options.append('all')

  if len(sys.argv[1:]) > 0:
    try:
      optlist, args = getopt.getopt(sys.argv[1:], '', options)
    except getopt.GetoptError, err:
      print(str(err))
      usage()
      sys.exit(2)

    command = optlist[0][0].replace('--', '')

    params = {}
    for param,value in optlist[1:]:
      params[param.replace('--', '')] = value

    if command == 'help' or 'help' in params:
      usage('all' in params)
      sys.exit(2)

    if hasattr(linode, command):
      func = getattr(linode, command)
      try:
        print(json.dumps(func(**params), indent=2))
      except api.MissingRequiredArgument, mra:
        print('Missing option --%s' % mra.value.lower())
        print('')
        usage()
        sys.exit(2)
    else:
      if not command == 'help':
        print('Invalid action '+optlist[0][0].lower())

      usage()
      sys.exit(2)
  else:
    console = LinodeConsole()

    console.runcode('import readline,rlcompleter,api,shell,json')
    console.runcode('readline.parse_and_bind("tab: complete")')
    console.runcode('readline.set_completer(shell.LinodeComplete().complete)')
    console.runcode('def pp(text=None): print(json.dumps(text, indent=2))')
    console.locals.update({'linode':linode})
    console.interact()
