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
import os
import os.path
import sqlite3

max_streams = 256

# XXX:
# host url table
# list sources
# manually add sources
# call mplayer

class Source:
    def __init__(self):
        self.source_url = ""
        self.host_url = ""
        self.server_name = ""

    def __str__(self):
        ret = ret + "  Source URL: %s\n" % (self.source_url)
        ret = ret + "  Host URL: %s\n" % (self.host_url)
        ret = ret + "  Server Name: %s\n" % (self.server_name)

        return ret

# scrapes icecast admin xml for sources
class SourceScraper:

    user="admin"

    def __init__(self, url):
        self.sources_l = []

        # XXX user should specify whole url actually
        self.host_url = "%s/admin/stats.xml" % url
        if not self.host_url.startswith("http://"):
            self.host_url = "http://%s" % self.host_url

        self.rq = None

    def parse(self):

        self.connect()

        xml = self.rq.read()
        soup = BeautifulSoup.BeautifulSoup(xml)
        sources = soup('source', limit=max_streams)

        sid = 0
        for s in sources:

            src = Source()
            src.source_url = s.listenurl.contents[0]

            try:
                src.server_name = s.server_name.contents[0]
            except:
                pass

            src.host_url = self.host_url

            self.sources_l.append(src)
            sid = sid + 1

    def connect(self):

        passwd = getpass.getpass()
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, self.host_url, self.user, passwd)
        auth = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(auth)

        urllib2.install_opener(opener)
        self.rq = urllib2.urlopen(self.host_url)

"""
Database convenience

All data is considered trusted, so no parametrised queries
"""
class Db:

    db_dir = "%s/.config/icefast" % (os.getenv("HOME"))
    db_file = "icefast.db"

    def __init__(self):

        # ensure path where db is to be stored exists
        if (not os.path.isdir(self.db_dir)):
            os.makedirs(self.db_dir)
            print("Creating '%s'" % self.db_dir)

        self.db = sqlite3.connect("%s/%s" % (self.db_dir, self.db_file))

        sql = "CREATE TABLE IF NOT EXISTS sources(sid INTEGER PRIMARY KEY, source_url " + \
                "TEXT, host_url TEXT, server_name TEXT);"
        self.db.execute(sql)

    def add_source(self, src):
        sql = "INSERT INTO sources (sid, source_url, host_url, server_name) " + \
            "VALUES (NULL, ?, ?, ?);"
        print(sql)
        self.db.execute(sql, (src.source_url, src.host_url, src.server_name));

    def commit(self):
        self.db.commit();

# command interpreter
class Interp:

    def __init__(self):
        # these have to be per instance so that functors can be derived
        self.cmds = {
            "add_source" : { "func" : self.cmd_add_source, "help" : "add_source <url>"},
            "ls" : { "func" : self.cmd_ls, "help" : "ls"},
            "pull" : { "func" : self.cmd_pull, "help" : "pull <url>"},
            "help" : {"func" : self.cmd_help, "help" : "help"},
        }

        self.db = Db()

    # add the source url 'src_url' 
    def cmd_add_source(self, src_url, origin_url):
        pass

    def cmd_ls(self):
        pass

    def cmd_pull(self, host_url):
        i = 0
        scraper = SourceScraper(host_url)
        scraper.parse()
        for src in scraper.sources_l:
            self.db.add_source(src)
            i = i + 1
        self.db.commit()

        print("Successully pulled %d sources!" % i)

    def cmd_help(self):
        print("\nAvailable commands:")
        for (cmd, info) in self.cmds.items():
            print(info["help"])
        print("")

    # interpret commands
    def interp(self):
        done = False
        cmd = None

        while (not done):
            sys.stdout.write("icefast> ")
            sys.stdout.flush()

            try:
                user_line = raw_input().split()
            except EOFError:
                done = True

            if not done:
                cmd = user_line[0]
                args = user_line[1:]
                try:
                    self.cmds[cmd]["func"](*args)
                #except TypeError:
                #    print("usage: %s" % self.cmds[cmd]["help"])
                except KeyError:
                    print("Parse error")
                    self.cmd_help()


            self.db.db.close()

if __name__ == "__main__":

    interp = Interp()
    interp.interp()
    print("\nbye!")
    #r = open_connection()
    #srcs = parse(r)

    #for s in srcs:
    #    print("%s\n" % s)
