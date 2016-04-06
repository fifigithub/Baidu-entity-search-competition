"""Experiments management scripts.

Managing past experiments with a database. It also contains Experiment to record experiment
data.
"""

import tabulate
import settings
import datetime
import tqdm
import json
import random
import gflags
import copy
import models
import numpy
import jinja2
import sqlite3

gflags.DEFINE_integer("cv_folds", 10, "folds of cross validations")
gflags.DEFINE_string("experiment_db_loc", "experiments.db", "Experimental Result database")


class ExperimentDB(object):

  def __init__(self, location):
    self.location = location
    self.connection = sqlite3.connect(location)
    self.cursor = self.connection.cursor()
    self._CreateTablesIfNotExist()

  the_db = None
  @staticmethod
  def GetTheDB():
    if ExperimentDB.the_db is None:
      ExperimentDB.the_db = ExperimentDB(gflags.FLAGS.experiment_db_loc)
    return ExperimentDB.the_db

  def _CreateTablesIfNotExist(self):
    self.cursor.execute("""
    create table if not exists experiments(
      exp_id integer primary key autoincrement,
      timestamp datetime,
      features string,
      avg_map real,
      celebrity real,
      movie real,
      restaurant real,
      tvShow real,
      cv_result text,
      hd_result text
    )""")
    self.connection.commit()

  def CreateNewExperiemnt(self):
    self.cursor.execute("insert into experiments(timestamp) values(?)", (
        datetime.datetime.now(),))
    exp_id = self.cursor.lastrowid
    self.connection.commit()
    return exp_id

  def SaveResult(
          self, exp_id, e_name_list, celebrity_score, movie_score, 
          restaurant_score, tvShow_score, cv_result, hd_result):
    self.cursor.execute(
        "update experiments set "
        "features=?, avg_map=?, celebrity=?, movie=?, restaurant=?, tvShow=?,"
        "cv_result=?, hd_result=? where exp_id=? ", (
          e_name_list,
          numpy.mean([celebrity_score, movie_score, restaurant_score, tvShow_score]),
          celebrity_score, movie_score, restaurant_score, tvShow_score,
          json.dumps(cv_result), json.dumps(hd_result), exp_id,
        )
    )
    self.connection.commit()


def _IterCVConfig(full_data, cv, seed=0):
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


class Experiment(object):

  def __init__(self, exp_id, e_name_list):
    self.cv_result = None
    self.hd_result = None
    self.exp_id = exp_id
    self.e_name_list = e_name_list

  def GetID(self):
    return self.exp_id

  def Save(self):
    exp_db = ExperimentDB.GetTheDB()
    exp_db.SaveResult(
        self.exp_id, self.e_name_list,
        self.hd_result["celebrity"]["score"],
        self.hd_result["movie"]["score"],
        self.hd_result["restaurant"]["score"],
        self.hd_result["tvShow"]["score"],
        self.cv_result,
        self.hd_result,
    )

  def RunCrossValidation(self, cv_data, seed=0):
    all_scores = dict((i, []) for i in settings.sub_tasks)
    all_query_results = dict((i, []) for i in settings.sub_tasks)

    for train_data, test_data in tqdm.tqdm(
        _IterCVConfig(cv_data, gflags.FLAGS.cv_folds),
        "Cross validating",
        gflags.FLAGS.cv_folds):
      model = models.BuildModel(self.e_name_list, train_data)
      result = model.EvaluateOn(test_data)
    
      for t in settings.sub_tasks:
        all_scores[t].append(result[t]["score"])
        all_query_results[t].extend(result[t]["query_results"])

    report_data = dict((i, {"score" : (None, None),}) for i in settings.sub_tasks)
    for t in settings.sub_tasks:
      scores = all_scores[t]
      query_results = all_query_results[t]
      report_data[t] = {"score" : (numpy.mean(scores), numpy.std(scores)),
                      "query_results" : query_results}

    self.cv_result = report_data

  def RecordHeldoutDataEval(self, hd_result):
    self.hd_result = hd_result

  def PrintSummary(self):
    print "Cross validation:"
    line = []
    for t in settings.sub_tasks:
      m, s = self.cv_result[t]["score"]
      line.append("%.2f+-%.2f" % (m, s))
    print tabulate.tabulate([line], headers=settings.sub_tasks)

    print
    print "Held-out set:"
    line = []
    for t in settings.sub_tasks:
      result = self.hd_result[t]["score"]
      line.append("%.2f" % result)
    print tabulate.tabulate([line], headers=settings.sub_tasks)

  def ExportReport(self, report_loc):
    report_data = {}
    report_data['CV_results'] = self.cv_result
    report_data['HD_results'] = self.hd_result
    report_data['sub_tasks'] = settings.sub_tasks

    template = jinja2.Template(open(gflags.FLAGS.report_template).read())
    with open(report_loc, 'w') as ofile:
      print >> ofile, template.render(report_data).encode('utf8')


def StartNewExperiment(e_name_list):
  exp_db = ExperimentDB.GetTheDB()
  exp_id = exp_db.CreateNewExperiemnt()
  return Experiment(exp_id, e_name_list)
