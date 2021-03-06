"""Models for reranking query results.

This module includes a logisitc regression model, which assigns a probability
for whether a result matches a query in a subtask.
"""

import copy
import gflags
import numpy
import random
import sklearn
import extractors
from sklearn import feature_extraction
from sklearn.externals import joblib
from sklearn import linear_model
from sklearn import cross_validation

gflags.DEFINE_string("models_dir", "models", "Directory to store models.")


def apk(actual, predicted, k=None):
  if k is None:
    k = len(predicted)
  if len(predicted)>k:
    predicted = predicted[:k]

  score = 0.0
  num_hits = 0.0

  for i,p in enumerate(predicted):
    if p in actual and p not in predicted[:i]:
      num_hits += 1.0
      score += num_hits / (i+1.0)

  if not actual:
    return 0.0

  return score / min(len(actual), k)


class LogisticModel(object):

  def __init__(self, extractors_name, train_data):
    self.extractors_name = extractors_name
    self.extractor = extractors.BuildExtractor(extractors_name)
    all_train_data = []
    for q_type, loaded_in_data in train_data.iteritems():
      all_train_data.extend([(q_type, i) for i in loaded_in_data])

    ml_train_data = []
    for q_type, (query, entity_info_list) in all_train_data:
      for ent, gs in entity_info_list:
        ml_train_data.append((dict(self.extractor((q_type, query), ent)), gs))

    v = feature_extraction.DictVectorizer()
    D = [d for d, y in ml_train_data]
    Y = numpy.array([int(y) for d, y in ml_train_data])
    X = v.fit_transform(D)
    logistic_regression = linear_model.LogisticRegression()

    self.logistic_model = logistic_regression.fit(X, Y)
    self.vectorizer = v

  def __getstate__(self):
    return (self.extractors_name, self.logistic_model, self.vectorizer)

  def __setstate__(self, state):
    self.extractors_name, self.logistic_model, self.vectorizer = state
    self.extractor = extractors.BuildExtractor(self.extractors_name)

  def Save(self, model_loc):
    joblib.dump(self, model_loc)

  @staticmethod
  def LoadFrom(model_loc):
    return joblib.load(model_loc)

  def EvaluateOn(self, test_data, seed=None):
    if seed is None:
      seed = random.Random()

    result = {}
    for sub_task, subtask_data in test_data.iteritems():
      result[sub_task] = self._EvaluateSubtaskData(sub_task, subtask_data, seed=seed)
    result["score"] = numpy.mean([i["score"] for i in result.itervalues()])
    
    return result

  
  def RankByModelProb(self, (subtask, q), results):
    return [r for s, r in sorted([
      (self.ScoreByModel((subtask, q), r), r) for r in results], reverse=True)]


  def ScoreByModel(self, (subtask, q), r):
    d = [dict(self.extractor((subtask, q), r))]
    x = self.vectorizer.transform(d)
    result = self.logistic_model.predict_proba(x)
    return result[0][1]


  def _EvaluateSubtaskData(self, subtask, subtask_data, seed=None):
    if seed is None:
      seed = random.Random()

    score_results = []
  
    report_data = {"query_results" : [], "score" : None}
  
    for q_id, (query, gs_result) in enumerate(subtask_data):
      shuffled_result = copy.copy(gs_result)
      seed.shuffle(shuffled_result)
      my_result = self.RankByModelProb(
        (subtask, query), [i for (i, t) in shuffled_result])
      gs_result = [i for i, t in gs_result if t == 1]
    
      report_item = {"term" : query, "ranked" : [], "id" : q_id}
      for r in my_result:
        report_item['ranked'].append(
          {'is_gs' : (r in gs_result), 'entity' : r})
      map_score = apk(gs_result, my_result, len(shuffled_result))
      report_item['MAP'] = map_score
      report_data["query_results"].append(report_item)
    
      score_results.append(map_score)
  
    map_value = sum(score_results) / len(score_results)
  
    report_data['map_value'] = map_value
    report_data['score'] = map_value
        
    return report_data



def BuildModel(extractor, train_data):
  return LogisticModel(extractor, train_data)
