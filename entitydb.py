"""Queries the baike entitydb to find entities.

The DB has only the following table:

CREATE TABLE entities(
  entity_name NUM,
  title NUM,
  link NUM,
  summary TEXT,
  content TEXT
);
CREATE UNIQUE INDEX entity_name on entities(entity_name);
"""


import gflags
import sqlite3
import unicodecsv as csv

gflags.DEFINE_string("baike_db_loc", "entities_db/baike.db",
                     "SQLite3 database containing the baike data")

class EntityDB(object):

  the_db = None

  def __init__(self):
    self.db_con = sqlite3.connect(gflags.FLAGS.baike_db_loc)
    self.cursor = self.db_con.cursor()

  @staticmethod
  def GetTheDB():
    if EntityDB.the_db is None:
      EntityDB.the_db = EntityDB()
    return EntityDB.the_db

  def _GetEntryByName(self, entity_name):
    self.cursor.execute(
      "select entity_name, summary, content from entities where entity_name=?", (entity_name,))
    row = self.cursor.fetchone()
    if row is None:
      raise IndexError
    entity_name, summary, content = row
    return {"entity_name" : entity_name,
            "summary" : summary,
            "content" : content}

  def LookupEntitySummary(self, entity_name):
    """Looks up entity in the summary dictionary.

    Raises:
      IndexError: when entity doesn't have an entry.
    """
    return self._GetEntryByName(entity_name)["summary"]


def LookupEntitySummary(entity_name):
  return EntityDB.GetTheDB().LookupEntitySummary(entity_name)
