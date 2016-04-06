"""Utility functions
"""

import errno
import os
import sys
import gflags


def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise


def Initialize():
  try:
    argv = gflags.FLAGS(sys.argv)
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  
def LoadInData(data_loc, test_data=False):
  lines = unicode(open(data_loc).read(), 'gbk').split('\n')
  parsing_result = []
  for line in lines:
    terms = line.split('\t')
    items = []
    for i in terms[1:]:
      if test_data:
        ent, score = i, None

      else:
        colon_separated = i.split(':')
        ent = ':'.join(colon_separated[:-1])
        score = int(colon_separated[-1])
      items.append((ent, score))
    if len(items) == 0:
      continue
    parsing_result.append((terms[0], items))
  return parsing_result
