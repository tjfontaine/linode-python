#!/usr/bin/python
"""
A quick script to verify that api.py is in sync with Linode's
published list of methods.

Copyright (c) 2010 Josh Wright <jshwright@gmail.com>
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

#The list of subsections found in the API documentation. This should
#probably be discovered automatically in the future
api_subsections = ('linode', 'nodebalancer', 'stackscript', 'dns', 'utility')

import api
import re
import itertools
from HTMLParser import HTMLParser
from urllib import unquote
from urllib2 import urlopen

class SubsectionParser(HTMLParser):
    base_url = 'http://www.linode.com/api/'

    def __init__(self, subsection):
        HTMLParser.__init__(self)
        self.subsection_re = re.compile('/api/%s/(.*)$' % subsection)
        self.methods = []
        url = self.base_url + subsection
        req = urlopen(url)
        self.feed(req.read())

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and attrs:
            attr_dict = dict(attrs)
            match = self.subsection_re.match(attr_dict.get('href', ''))
            if match:
                self.methods.append(unquote(match.group(1)).replace('.','_'))

local_methods = api.Api.valid_commands()
remote_methods = list(itertools.chain(*[SubsectionParser(subsection).methods for subsection in api_subsections]))

# Cross-check!
for i in local_methods:
    if i not in remote_methods:
        print('REMOTE Missing: ' + i)
for i in remote_methods:
    if i not in local_methods:
        print('LOCAL Missing:  ' + i)

