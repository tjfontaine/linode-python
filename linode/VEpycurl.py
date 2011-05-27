"""
Copyright (C) 2009, Kenneth East
 
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
 
#
# module for VEpycurl - the Very Easy interface to pycurl
#
 
from StringIO import StringIO
import urllib
import pycurl
import sys
import os
 
class VEpycurl() :
    """
    A VERY EASY interface to pycurl, v1.0
    Tested on 22Feb09 with python 2.5.1, py25-curl 7.19.0, libcurl/7.19.2, OS-X 10.5.6
    """
 
    def __init__(self,
                 userAgent      = 'Mozilla/4.0 (compatible; MSIE 8.0)',
                 followLocation = 1,            # follow redirects?
                 autoReferer    = 1,            # allow 'referer' to be set normally?
                 verifySSL      = 0,            # tell SSL to verify IDs?
                 useCookies     = True,         # will hold all pycurl cookies
                 useSOCKS       = False,        # use SOCKS5 proxy?
                 proxy          = 'localhost',  # SOCKS host
                 proxyPort      = 8080,         # SOCKS port
                 proxyType      = 5,            # SOCKS protocol
                 verbose        = False,
                 debug          = False,
                 ) :
        self.followLocation = followLocation
        self.autoReferer    = autoReferer
        self.verifySSL      = verifySSL
        self.useCookies     = useCookies
        self.useSOCKS       = useSOCKS
        self.proxy          = proxy
        self.proxyPort      = proxyPort
        self.proxyType      = proxyType
        self.pco = pycurl.Curl()
        self.pco.setopt(pycurl.USERAGENT,      userAgent)
        self.pco.setopt(pycurl.FOLLOWLOCATION, followLocation)
        self.pco.setopt(pycurl.MAXREDIRS,      20)
        self.pco.setopt(pycurl.CONNECTTIMEOUT, 30)
        self.pco.setopt(pycurl.AUTOREFERER,    autoReferer)
        # SSL verification (True/False)
        self.pco.setopt(pycurl.SSL_VERIFYPEER, verifySSL)
        self.pco.setopt(pycurl.SSL_VERIFYHOST, verifySSL)
        if useCookies == True :
            cjf = os.tmpfile() # potential security risk here; see python documentation
            self.pco.setopt(pycurl.COOKIEFILE, cjf.name)
            self.pco.setopt(pycurl.COOKIEJAR,  cjf.name)
        if useSOCKS :
            # if you wish to use SOCKS, it is configured through these parms
            self.pco.setopt(pycurl.PROXY,     proxy)
            self.pco.setopt(pycurl.PROXYPORT, proxyPort)
            self.pco.setopt(pycurl.PROXYTYPE, proxyType)
        if verbose :
            self.pco.setopt(pycurl.VERBOSE, 1)
        if debug :
            print 'PyCurl version info:'
            print pycurl.version_info()
            print
            self.pco.setopt(pycurl.DEBUGFUNCTION, self.debug)
        return
 
    def perform(self, url, fields=None, headers=None) :
        if fields :
            # This is a POST and we have fields to handle
            fields = urllib.urlencode(fields)
            self.pco.setopt(pycurl.POST,       1)
            self.pco.setopt(pycurl.POSTFIELDS, fields)
        else :
            # This is a GET, and we do nothing with fields
            pass
        pageContents = StringIO()
        self.pco.setopt(pycurl.WRITEFUNCTION,  pageContents.write)
        self.pco.setopt(pycurl.URL, url)
        if headers :
            self.pco.setopt(pycurl.HTTPHEADER, headers)
        self.pco.perform()
        self.pco.close()
        self.pc = pageContents
        return
 
    def results(self) :
        # return the page contents that were received in the most recent perform()
        # self.pc is a StringIO object
        self.pc.seek(0)
        return self.pc
 
    def debug(self, debug_type, debug_msg) :
        print 'debug(%d): %s' % (debug_type, debug_msg)
        return
 
try:
    # only call this once in a process.  see libcurl docs for more info.
    pycurl.global_init(pycurl.GLOBAL_ALL)
except:
    print 'Fatal error: call to pycurl.global_init() failed for some reason'
    sys.exit(1)
