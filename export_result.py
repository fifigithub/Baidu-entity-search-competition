"""Exporting results for submission
"""

#!/usr/bin/python

import gflags
import utils
import models
import settings
import tqdm
from os import path


gflags.DEFINE_integer("model_id", 101,
                      "ID of the model used to calculate submission results")
gflags.DEFINE_string("test_data_loc_template", "data/DEV SET/{}.DEVSET.txt",
                     "Format template of dataset in a subtask.")
gflags.DEFINE_string("output_dir", "output",
                     "directory to export output. ")
gflags.DEFINE_string("results_limits", "restaurant:70",
                     "Comma separated list, specifying how many results I should export. "
                     "Default to export all.")


def LoadTestData():
  data = {}
  for task in settings.sub_tasks:
    data_loc = gflags.FLAGS.test_data_loc_template.format(task)
    data[task] = utils.LoadInData(data_loc, test_data=True)
  return data


def ExportResult(model, testdata, subtask, output_filename, result_limit=None):
  with open(output_filename, 'w') as ofile:
    for query, entries in tqdm.tqdm(testdata, "Exporting results for {}".format(subtask)):
      my_result = model.RankByModelProb((subtask, query), [i for (i, t) in entries])
      if result_limit:
        my_result = my_result[:result_limit]
      print >> ofile, '\t'.join([query] + my_result).encode('gbk')


def main():
  utils.Initialize()

  model_loc = "{}/{}.model".format("models", gflags.FLAGS.model_id)
  if not path.isfile(model_loc):
    raise ValueError("Cannot find model {}".format(model_loc))

  model = models.LogisticModel.LoadFrom(model_loc)

  testdata = LoadTestData()

  limits = dict(
      i.split(":") for i in gflags.FLAGS.results_limits.split(","))
  limits = dict((k, int(v)) for k, v in limits.iteritems())

  utils.mkdir_p(gflags.FLAGS.output_dir)
  for subtask in settings.sub_tasks:
    output_filename = path.join(gflags.FLAGS.output_dir, subtask + ".txt")
    ExportResult(model, testdata[subtask], subtask, output_filename,
                 result_limit=limits.get(subtask, None))

if __name__ == "__main__":
  main()
