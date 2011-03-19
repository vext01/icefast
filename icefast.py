#!/usr/bin/env python

"""
Copyright (c) 2011, Edd Barrett <vext01@gmail.com>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import urllib2
import sys
import BeautifulSoup
import getpass

max_streams = 256

class Source:
    def __init__(self):
        self.sid = None
        self.url = None
        self.desc = None
        self.server_name = None
        self.server_type = None # mime type
        self.sub_type= None # codec

    def __str__(self):
        ret = "Source -[#%03d]-\n" % (self.sid)
        ret = ret + "  URL: %s\n" % (self.url)
        ret = ret + "  Description: %s\n" % (self.url)
        ret = ret + "  Server Name: %s\n" % (self.server_name)
        ret = ret + "  Server Type: %s\n" % (self.server_type)
        ret = ret + "  Sub Type: %s" % (self.sub_type)

        return ret

def parse(rq):

    sources_l = []

    xml = rq.read()
    soup = BeautifulSoup.BeautifulSoup(xml)
    sources = soup('source', limit=max_streams)

    sid = 0
    for s in sources:

        src = Source()
        src.sid = sid
        src.url = s.listenurl.contents[0]

        try:
            src.desc = s.server_description.contents[0]
        except:
            pass

        try:
            src.server_name = s.server_name.contents[0]
        except:
            pass

        try:
            src.server_type = s.server_type.contents[0]
        except:
            pass

        try:
            src.sub_type = s.subtype.contents[0]
        except:
            pass

        sources_l.append(src)
        sid = sid + 1

    return sources_l

def open_connection():

    # XXX config file
    user="admin"
    passwd=getpass.getpass()
    url="http://localhost:8005/admin/stats.xml"

    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, user, passwd)
    auth = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(auth)

    urllib2.install_opener(opener)
    rq = urllib2.urlopen(url)

    return rq

if __name__ == "__main__":
    r = open_connection()
    srcs = parse(r)

    for s in srcs:
        print("%s\n" % s)
