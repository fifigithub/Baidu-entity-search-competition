"""
Grabbing Baidu Baike for entity definitions.

This script grabs all entities in the entity directory, and put them into --db_loc.
It grabs everything in a multi-threading fashion. The first time some fetching attmpts may fail,
so we need several runs to guarantee every entity has some data.

First time:
  # python grab_entities.py --retry_on_failed=false

You may then see how many entries were not fetched by:
  # sqlite3 entities_db/entities.db 'select count(*) from search_results where failed'

When the number is not 0, iteratively try for a couple of times:
  # python grab_entities.py
"""

import os
from os import path
import sqlite3
import threading
import Queue
import urllib
import sys
from bs4 import BeautifulSoup
import gflags

gflags.DEFINE_boolean("retry_on_failed", True, "When set, will only retry on failed entities.")
gflags.DEFINE_string("db_loc", "entities_db/entities.db", 
                     "When set, will only retry on failed entities.")
gflags.DEFINE_integer("n_fetching_threads", 500, "Number of threads to retrieve results.")
gflags.DEFINE_string("entity_dir", "data/ENTITY SET", "Directory containing entities.")

def GetAllEntities():
    filenames = [path.join(gflags.FLAGS.entity_dir, fname) for fname in os.listdir(
        gflags.FLAGS.entity_dir)]
    all_entities = []
    for fname in filenames:
        with open(fname) as infile:
            content = unicode(infile.read(), 'gbk')
            all_entities.extend([i for i in content.split('\n') if len(i.strip()) != 0])
    all_entities = set(all_entities)
    return all_entities


def SearchForEntityName(name):
    request_template = 'http://baike.baidu.com/search?%s'
    #urllib.urlopen('')
    args = urllib.urlencode({"word" : name.encode('utf8'), 'pn' : 0, 'rn' : 0, 'enc' : 'utf8'})
    request = request_template % args

    response = urllib.urlopen(request).read()
    return unicode(response, 'utf8', 'ignore')

task_queue = Queue.Queue()
writing_queue = Queue.Queue()

class FetchingThread(threading.Thread):
    def run(self):
        while True:
            name = task_queue.get()    
            if name is None:
                break
            writing_queue.put(self.TryFetchingResult(name))

    def TryFetchingResult(self, name):
        try:
            result = SearchForEntityName(name)
            return (name, result, False)
        except Exception, e:
            return (name, str(e), True)

class WritingThread(threading.Thread):
    
    def __init__(self, db_loc, len_all_entities, modify=False):
        threading.Thread.__init__(self)
        self.db_loc = db_loc
        self.len_all_entities = len_all_entities
        self.modify = modify

    def run(self):
        conn = sqlite3.connect(self.db_loc)
        cursor = conn.cursor()
        if not self.modify:
            cursor.execute(
                'create table search_results(entity_name text, response text, failed bool)')
            cursor.execute('create index ent_name on search_results(entity_name);')
            conn.commit()

        def EntityNameAlreadyOccur(ename):
            cursor.execute('select count(*) from search_results where entity_name=?' , (ename,))
            (n_occur, ) = cursor.fetchone()
            return (n_occur > 0)
        
        n_finished = 0
        while n_finished < self.len_all_entities:
            entity_name, text, failed = writing_queue.get()
            
            if not self.modify or not EntityNameAlreadyOccur(entity_name):
                cursor.execute(
                    'insert into search_results values (?, ?, ?)', (entity_name, text, failed))
            else:
                cursor.execute(
                    'update search_results set response=?,failed=? where entity_name=?', (
                        text, failed, entity_name))
            n_finished += 1
            if n_finished % 100 == 0:
                print "finished %d, out of %d" % (n_finished, self.len_all_entities)
                conn.commit()
        conn.commit()

def GetFailedEntities(loc):
    conn = sqlite3.connect(loc)
    cursor = conn.cursor()
    successful_entities = [i[0] for i in cursor.execute(
        'select entity_name from search_results where not failed')]
    failed_entities = set(GetAllEntities()) - set(successful_entities)
    return failed_entities
    

def main(argv):
    try:
        argv = gflags.FLAGS(argv)  # parse flags
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], gflags.FLAGS)
        sys.exit(1)

    e_db_loc = path.abspath(gflags.FLAGS.db_loc)
    if not gflags.FLAGS.retry_on_failed:
        all_entities = GetAllEntities()
    else:
        all_entities = GetFailedEntities(e_db_loc)

    fetching_threads = [FetchingThread() for i in range(gflags.FLAGS.n_fetching_threads)]
    writing_thread = WritingThread(e_db_loc, len(all_entities), gflags.FLAGS.retry_on_failed)

    for t in fetching_threads + [writing_thread]:
        t.start()
    for ent in all_entities:
        task_queue.put(ent)
    for i in range(gflags.FLAGS.n_fetching_threads):
        task_queue.put(None)
    
    writing_thread.join()

if __name__ == "__main__":
    main(sys.argv)
