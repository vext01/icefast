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
        self.sid = None
        self.source_url = ""
        self.host_url = ""
        self.server_name = ""

    def __init__(self, sid, source_url, host_url, server_name):
        self.sid = sid
        self.source_url = source_url
        self.host_url = host_url
        self.server_name = server_name

    def __str__(self):
        ret = "  SID: %d\n" % (self.sid)
        ret = ret + "  Source URL: %s\n" % (self.source_url)
        ret = ret + "  Host URL: %s\n" % (self.host_url)
        ret = ret + "  Server Name: %s" % (self.server_name)

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

        for s in sources:

            src = Source()
            src.source_url = s.listenurl.contents[0]

            try:
                src.server_name = s.server_name.contents[0]
            except:
                pass

            src.host_url = self.host_url
            self.sources_l.append(src)

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

        curs = self.db.cursor()
        sql = "CREATE TABLE IF NOT EXISTS sources" + \
            "(sid INTEGER PRIMARY KEY, source_url " + \
            "TEXT, host_url TEXT, server_name TEXT);"
        curs.execute(sql)

    def add_source(self, src):
        sql = "INSERT INTO sources (sid, source_url, host_url, server_name) " + \
            "VALUES (NULL, ?, ?, ?);"
        print(sql)
        self.db.execute(sql, (src.source_url, src.host_url, src.server_name));

    def commit(self):
        self.db.commit();

    def get_source(self, sid):
        curs = self.db.cursor()
        sql = "SELECT sid, source_url, host_url, server_name FROM sources " + \
            "WHERE sid = %s;" % (sid)
        curs.execute(sql);
        one = curs.fetchone()

        ret = None if one == None else Source(*one)
        return ret

    def get_sources(self, filt = None):
        curs = self.db.cursor()

        if filt == None:
            sql = "SELECT sid, source_url, host_url, server_name FROM sources;"
        else:
            sql = ("SELECT sid, source_url, host_url, server_name " + \
                    "FROM sources WHERE sid LIKE '%%%s%%' " + \
                    "OR source_url LIKE '%%%s%%' OR host_url LIKE '%%%s%%' " + \
                    "OR server_name LIKE '%%%s%%';") % (filt, filt, filt, filt)

        curs.execute(sql)
        
        srcs = []
        while (True):

            s = curs.fetchone()
            if s == None:
                break

            s_o = Source(*s)
            srcs.append(s_o)

        return srcs

# command interpreter
class Interp:

    def __init__(self):
        # these have to be per instance so that functors can be derived
        self.cmds = {
            "add_source" : { "func" : self.cmd_add_source, 
                "help" : "add_source <url>"},
            "ls" : {"func" : self.cmd_ls, "help" : "ls [filter]"},
            "pull" : {"func" : self.cmd_pull, "help" : "pull <url>"},
            "help" : {"func" : self.cmd_help, "help" : "help"},
            "play" : {"func" : self.cmd_play, "help" : "play <sid>"},
        }

        self.db = Db()

    # add the source url 'src_url' 
    def cmd_add_source(self, src_url, origin_url):
        pass

    def cmd_ls(self, filt = None):
        sources = self.db.get_sources(filt)
        for i in sources:
            print("%s\n" % str(i))

    def cmd_pull(self, host_url):
        scraper = SourceScraper(host_url)
        scraper.parse()
        for src in scraper.sources_l:
            self.db.add_source(src)
        self.db.commit()

        print("Successully pulled %d sources!" % i)

    def cmd_help(self):
        print("\nAvailable commands:")
        for (cmd, info) in self.cmds.items():
            print(info["help"])
        print("")

    def cmd_play(self, sid):
        src = self.db.get_source(sid)

        if (src == None):
            print("No source found")
            return

        os.system("mplayer -cache 512 %s" % (src.source_url))

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
                #try:
                self.cmds[cmd]["func"](*args)
                #except TypeError:
                #    print("usage: %s" % self.cmds[cmd]["help"])
                #except KeyError:
                #    print("Parse error")
                #    self.cmd_help()

        self.db.db.close()

if __name__ == "__main__":

    interp = Interp()
    interp.interp()
    print("\nbye!")
    #r = open_connection()
    #srcs = parse(r)

    #for s in srcs:
    #    print("%s\n" % s)
