"""Running an experiment on feature extraction method.

The script carries out a 10-fold cross-validation, as well as an evaluation on
held-out data. It also stores the trained model to the models/ directory. HTML
reports for debugging purposes are exported to reports/.

Example:
  python run_experiments.py --extractors=nchar
"""

import sys
import gflags
import settings
import tabulate
import extractors
import numpy
import random
import copy
import jinja2
import models
import unicodecsv as csv
from os import path


gflags.DEFINE_string("extractors", "nchar,char,nsumchar,sumchar",
                     "Extractors to use for experiemnt")
gflags.DEFINE_string("reports_dir", "reports", "Directory to store reports.")
gflags.DEFINE_string("models_dir", "models", "Directory to store models.")
gflags.DEFINE_string("report_template", "html/error_analysis.html",
                     "Template for error analysis.")
gflags.DEFINE_string("cv_data_loc_template", "data/TRAIN SET/{}.cv.txt",
                     "Template for cross validation data location. Later call .format.")
gflags.DEFINE_string("hd_data_loc_template", "data/TRAIN SET/{}.holdout.txt",
                     "Template for held-out data location. Later call .format.")


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


def LoadCVData():
  data = {}
  for task in settings.sub_tasks:
    data_loc = gflags.FLAGS.cv_data_loc_template.format(task)
    data[task] = LoadInData(data_loc, test_data=False)
  return data

def LoadHDData():
  data = {}
  for task in settings.sub_tasks:
    data_loc = gflags.FLAGS.hd_data_loc_template.format(task)
    data[task] = LoadInData(data_loc, test_data=True)
  return data


def _IterCVConfig(full_data, cv=10, seed=0):
  splitted = {}
  rdm = random.Random(seed)
  for task_name, data in full_data.iteritems():
    splitted[task_name] = []
    shuffled_data = copy.copy(data)
    rdm.shuffle(shuffled_data)
    
    l = len(data)
    for i in range(cv):
      start = i * l / cv
      end = (i + 1) * l / cv
      the_slice = shuffled_data[start:end]
      splitted[task_name].append(the_slice)

  for i in range(cv):
    train_data = dict((t, []) for t in settings.sub_tasks)
    for j in range(cv):
      if j != i:
        for t in settings.sub_tasks:
          train_data[t].extend(splitted[t][j])
    test_data = dict((t, splitted[t][i]) for t in settings.sub_tasks)
    yield (train_data, test_data)


def RunCrossValidation(extractor, cv_data, seed=0):
  all_results = dict((i, []) for i in settings.sub_tasks)
  for train_data, test_data in _IterCVConfig(cv_data):
    model = models.BuildModel(extractor, train_data)
    result = model.EvaluateOn(test_data)
    
    for t in settings.sub_tasks:
      all_results[t].append(result[t]["score"])

  report_data = dict((i, {"score" : (None, None),}) for i in settings.sub_tasks)
  for t, scores in all_results.iteritems():
    report_data[t] = (numpy.mean(scores), numpy.std(scores))

  return report_data


def main(argv):
  try:
    argv = gflags.FLAGS(argv)
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  e_name_list = gflags.FLAGS.extractors.split(',')
  extractor = extractors.BuildExtractor(e_name_list)

  # TODO(xuehuichao): Actually implement the central experiments database.
  experiment_id = 101
  report_loc = path.join(gflags.FLAGS.reports_dir, "%.3d.html" % experiment_id)
  model_loc = path.join(gflags.FLAGS.models_dir, "%.3d.model" % experiment_id)

  print "Experiment ID: %d. Detailed report at %s. Model at %s\n" % (
      experiment_id,
      report_loc,
      model_loc,
  )
  
  report_data = {
      "CV_results" : {},
      "HD_results" : {}
  }
  cv_data = LoadCVData()
  hd_data = LoadHDData()
  report_data['CV_results'] = RunCrossValidation(extractor, cv_data)
  model = models.BuildModel(extractor, cv_data)
  report_data['HD_results'] = model.EvaluateOn(hd_data)

  model.Save(model_loc)
  
  # Print out summary
  print "Cross validation:"
  line = []
  for t in settings.sub_tasks:
    m, s = report_data['CV_results'][t]["score"]
    line.append("%.2f+-%.2f" % (m, s))
  print tabulate([line], headers=settings.sub_tasks)

  print
  print "Held-out set:"
  line = []
  for t in settings.sub_tasks:
    result = report_data['HD_results'][t]["score"]
    line.append("%.2f" % result)
  print tabulate([line], headers=settings.sub_tasks)

  # Write report
  template = jinja2.Template(open(gflags.FLAGS.report_template).read())
  with open(report_loc, 'w') as ofile:
    print >> ofile, template.render(report_data).encode('utf8')

if __name__ == "__main__":
  main(sys.argv)
