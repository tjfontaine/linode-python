#!/usr/bin/python
"""
A quick script to verify that api.py is in sync with Linode's
published list of methods.

Copyright (c) 2009 Ryan Tucker <rtucker@gmail.com>

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

# URL of API documentation
apidocurl = 'http://www.linode.com/api/autodoc.cfm'

import api
import re
import urllib

tmpfile, httpheaders = urllib.urlretrieve(apidocurl)
tmpfd = open(tmpfile)

local_methods = api.Api.valid_commands()
remote_methods = []

# Read in the list of methods Linode has
rg = re.compile('.*?\\?method=((?:[a-z][a-z\\.\\d\\-]+)\\.(?:[a-z][a-z\\-]+))(?![\\w\\.])')

for i in tmpfd.readlines():
    m = rg.search(i)
    if m:
        remote_methods.append(m.group(1).replace('.','_'))

# Cross-check!
for i in local_methods:
    if i not in remote_methods:
        print 'REMOTE Missing: ' + i
for i in remote_methods:
    if i not in local_methods:
        print 'LOCAL Missing:  ' + i

