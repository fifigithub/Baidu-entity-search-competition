import unicodecsv as csv
import urllib
import logging
import threading
import Queue
import time
from bs4 import BeautifulSoup
import tqdm
baike_file = 'entities_db/baike.csv'

link_data = dict((line['entity_name'], line['link'])for line in csv.DictReader(open(baike_file)) if line['link'])

def FetchLink(link):
  n_retry = 0
  while n_retry <= 3:
    try:
      page = urllib.urlopen(link).read()
      soup = BeautifulSoup(page)
      text = "\n".join([i.text for i in soup('div', {'class' : 'para'})])
      return text
    except Exception, e:
      logging.error("Error retrieving %s, %s", link, e)
      n_retry += 1
      time.sleep(3)
  logging.error("Gave up %s", link)
  return None

task_queue = Queue.Queue()
write_queue = Queue.Queue()

class Worker(threading.Thread):
  def run(self):
    while True:
      name, link = task_queue.get()
      content = FetchLink(link)
      write_queue.put((name, content))
      
class Writer(threading.Thread):
  def __init__(self, outputfile, total_n):
    threading.Thread.__init__(self)
    self.outfile = open(outputfile, 'w')
    self.writer = csv.DictWriter(self.outfile, ['entity_name', 'content'])
    self.writer.writeheader()
    self.total_n = total_n
  
  def run(self):
    for i in tqdm.tqdm(range(self.total_n)):
      name, content = write_queue.get()
      self.writer.writerow({'entity_name' : name, 'content' : content})
      self.outfile.flush()

workers = [Worker() for i in range(100)]
writer = Writer("entities_db/baike_content.csv", len(link_data))

for w in workers + [writer]:
  w.start()

for ename, link in link_data.iteritems():
  task_queue.put((ename, link))

writer.join()
