#!/usr/bin/env python
"""
A Script to deploy a bunch of Linodes from a given stackscript

Copyright (c) 2011 Timothy J Fontaine <tjfontaine@gmail.com>

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

import json
import logging
import os.path
import re
import sys

from optparse import OptionParser
from getpass import getpass
from os import environ, linesep

import api

parser = OptionParser()
parser.add_option('-d', '--datacenter', dest="datacenter",
  help="datacenter to deploy to", metavar='DATACENTERID',
  action="store", type="int",
  )
parser.add_option('-c', '--count', dest="count",
  help="how many nodes to deploy", metavar="COUNT",
  action="store", type="int",
  )
parser.add_option('-s', '--stackscript', dest='stackscript',
  help='stackscript to deploy', metavar='STACKSCRIPTID',
  action='store', type='int',
  )
parser.add_option('-f', '--filename', dest='filename',
  help='filename with stackscript options', metavar='FILENAME',
  action='store',
  )
parser.add_option('-p', '--plan', dest='plan',
  help='linode plan that these nodes should be', metavar='PLANID',
  action='store', type='int',
  )
parser.add_option('-t', '--term', dest='term',
  help='payment term', metavar='TERM',
  action='store', type='choice', choices=('1','12','24'),
  )
parser.add_option('-D', '--distribution', dest='distribution',
  help='distribution to base deployment on', metavar='DISTRIBUTIONID',
  action='store', type='int',
  )
parser.add_option('-S', '--disksize', dest='disksize',
  help='size of the disk (in mb) that the stackscript should create',
  metavar='DISKSIZE', action='store', type='int',
  )
parser.add_option('-v', '--verbose', dest='verbose',
  help='enable debug logging in the api', action="store_true",
  default=False,
  )
parser.add_option('-k', '--kernel', dest='kernel',
  help='the kernel to assign to the configuration', metavar='KERNELID',
  action='store', type='int',
  )
parser.add_option('-B', '--boot', dest='boot',
  help='whether or not to issue a boot after a node is created',
  action='store_true', default=False,
  )

(options, args) = parser.parse_args()

if options.verbose:
  logging.basicConfig(level=logging.DEBUG)

try:
  if not options.count:
    raise Exception('Must specify how many nodes to create')

  if not options.datacenter:
    raise Exception('Must specify which datacenter to create nodes in')

  if not options.stackscript:
    raise Exception('Must specify which stackscript to deploy from')

  if not options.filename:
    raise Exception('Must specify filename of stackscript options')

  if not options.plan:
    raise Exception('Must specify the planid')

  if not options.term:
    raise Exception('Must speficy the payment term')

  if not options.distribution:
    raise Exception('Must speficy the distribution to deploy from')

  if not options.disksize:
    raise Exception('Must speficy the size of the disk to create')

  if not os.path.exists(options.filename):
    raise Exception('Options file must exist')

  if not options.kernel:
    raise Exception('Must specify a kernel to use for configuration')
except Exception, ex:
  sys.stderr.write(str(ex) + linesep)
  parser.print_help()
  sys.exit('All options are required (yes I see the contradiction)')

json_file = open(options.filename)

# Round trip to make sure we are valid
json_result = json.load(json_file)
stackscript_options = json.dumps(json_result)

if 'LINODE_API_KEY' in environ:
  api_key = environ['LINODE_API_KEY']
else:
  api_key = getpass('Enter API Key: ')

print 'Passwords  must contain at least two of these four character classes: lower case letters - upper case letters - numbers - punctuation'
root_pass = getpass('Enter the root password for all resulting nodes: ')
root_pass2 = getpass('Re-Enter the root password: ')

if root_pass != root_pass2:
  sys.exit('Passwords must match')

valid_pass = 0

if re.search(r'[A-Z]', root_pass):
  valid_pass += 1

if re.search(r'[a-z]', root_pass):
  valid_pass += 1

if re.search(r'[0-9]', root_pass):
  valid_pass += 1

if re.search(r'\W', root_pass):
  valid_pass += 1

if valid_pass < 2:
  sys.exit('Password too simple, only %d of 4 classes found' % (valid_pass))

linode_api = api.Api(api_key, batching=True)

needFlush = False

created_linodes = []

def deploy_set():
  linode_order = []
  for r in linode_api.batchFlush():
    # TODO XXX FIXME handle error states
    linodeid = r['DATA']['LinodeID']
    created_linodes.append(linodeid)
    linode_order.append(linodeid)
    linode_api.linode_disk_createfromstackscript(
      LinodeID=linodeid,
      StackScriptID=options.stackscript,
      StackScriptUDFResponses=stackscript_options,
      DistributionID=options.distribution,
      Label='From stackscript %d' % (options.stackscript),
      Size=options.disksize,
      rootPass=root_pass,
    )
  to_boot = []
  for r in linode_api.batchFlush():
    # TODO XXX FIXME handle error states
    linodeid = linode_order.pop(0)
    diskid = [str(r['DATA']['DiskID'])]
    for i in range(8): diskid.append('')
    linode_api.linode_config_create(
      LinodeID=linodeid,
      KernelID=options.kernel,
      Label='From stackscript %d' % (options.stackscript),
      DiskList=','.join(diskid),
    )
    if options.boot:
      to_boot.append(linodeid)
  linode_api.batchFlush()

  for l in to_boot:
    linode_api.linode_boot(LinodeID=l)

  if len(to_boot):
    linode_api.batchFlush()

for i in range(options.count):
  if needFlush and i % 25 == 0:
    needFlush = False
    deploy_set()
    
  linode_api.linode_create(
        DatacenterID=options.datacenter,
        PlanID=options.plan,
        PaymentTerm=options.term,
  )
  needFlush = True

if needFlush:
  needFlush = False
  deploy_set()

print 'List of created Linodes:'
print '[%s]' % (', '.join([str(l) for l in created_linodes]))
