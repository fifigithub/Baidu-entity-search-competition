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
        "select E.exp_id, E.features, E.avg_map, "
        "E.celebrity, E.movie, E.restaurant, E.tvShow, E.timestamp from experiments as E inner join "
        "(select exp_id, max(timestamp) from experiments group by features) b "
        "on E.exp_id = b.exp_id order by E.avg_map desc"))
  print tabulate.tabulate(
      latest_results,
      headers=["ID", "features", "MAP", "Celebrity", "Movie", "Restaurant", "tvShow", "time"])


if __name__ == "__main__":
  main()
