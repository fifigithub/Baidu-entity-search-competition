import gflags
import unicodecsv as csv

gflags.DEFINE_string("baike_csv_loc", "entities_db/baike.csv",
                     "Location of the Baike CSV file, containing the snippets.")

class EntityDB(object):

  the_db = None

  def __init__(self):
    self.entity_summary_map = dict()
    with open(gflags.FLAGS.baike_csv_loc) as infile:
      for row in csv.DictReader(infile):
        name = row['entity_name']
        summary = row['summary']
        self.entity_summary_map[name] = summary


  @staticmethod
  def GetTheDB():
    if EntityDB.the_db is None:
      EntityDB.the_db = EntityDB()
    return EntityDB.the_db

  def LookupEntitySummary(self, entity_name):
    """Looks up entity in the summary dictionary.

    Raises:
      IndexError: when entity doesn't have an entry.
    """
    return self.entity_summary_map[entity_name]


def LookupEntitySummary(entity_name):
  return EntityDB.GetTheDB().LookupEntitySummary(entity_name)
