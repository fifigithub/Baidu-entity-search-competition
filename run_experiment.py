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
import extractors
import models
import utils
import experiments
import unicodecsv as csv
from os import path


gflags.DEFINE_string("extractors",
                     "nchar,char,nsumchar,sumchar,cont_bigram,cont_match",
                     "Extractors to use for experiemnt")
gflags.DEFINE_string("reports_dir", "reports", "Directory to store reports.")
gflags.DEFINE_string("report_template", "html/exp_report.html",
                     "Template for error analysis.")
gflags.DEFINE_string("cv_data_loc_template", "data/TRAIN SET/{}.cv.txt",
                     "Template for cross validation data location. Later call"
                     " .format.")
gflags.DEFINE_string("hd_data_loc_template", "data/TRAIN SET/{}.holdout.txt",
                     "Template for held-out data location. Later call .format.")


def LoadCVData():
  data = {}
  for task in settings.sub_tasks:
    data_loc = gflags.FLAGS.cv_data_loc_template.format(task)
    data[task] = utils.LoadInData(data_loc, test_data=False)
  return data

def LoadHDData():
  data = {}
  for task in settings.sub_tasks:
    data_loc = gflags.FLAGS.hd_data_loc_template.format(task)
    data[task] = utils.LoadInData(data_loc, test_data=False)
  return data


def main():
  utils.Initialize()
  e_name_list = gflags.FLAGS.extractors

  new_experiment = experiments.StartNewExperiment(e_name_list)
  experiment_id = new_experiment.GetID()
  utils.mkdir_p(gflags.FLAGS.reports_dir)
  utils.mkdir_p(gflags.FLAGS.models_dir)
  report_loc = path.join(gflags.FLAGS.reports_dir, "%.3d.html" % experiment_id)
  model_loc = path.join(gflags.FLAGS.models_dir, "%.3d.model" % experiment_id)

  print "Experiment ID: %d. Detailed report at %s. Model at %s\n" % (
      experiment_id,
      report_loc,
      model_loc,
  )
  
  cv_data = LoadCVData()
  hd_data = LoadHDData()

  new_experiment.RunCrossValidation(cv_data)

  model = models.BuildModel(e_name_list, cv_data)
  model.Save(model_loc)
  hd_result = model.EvaluateOn(hd_data)
  new_experiment.RecordHeldoutDataEval(hd_result)

  new_experiment.Save()
  new_experiment.PrintSummary()
  new_experiment.ExportReport(report_loc)

  
if __name__ == "__main__":
  main()
