import gflags
import experiments
import tabulate
import utils
import sqlite3


def main():
  utils.Initialize()
  connection = sqlite3.connect(gflags.FLAGS.experiment_db_loc)
  cursor = connection.cursor()
  latest_results = list(
      cursor.execute(
          "select exp_id, max(timestamp), avg_map, "
          "celebrity, movie, restaurant, tvShow from experiments group by features"))
  print tabulate.tabulate(
      latest_results,
      headers=["ID", "Time", "MAP", "Celebrity", "Movie", "Restaurant", "tvShow"])

if __name__ == "__main__":
  main()
