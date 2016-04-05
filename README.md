# Baidu-project

This project is for Baidu's entity search competition:

* Rules are [here](http://nlpcc.baidu.com/rules.html)
* Data are in data/ directory.

We are the Chitu team! -- [Link](http://fifigithub.github.io/Baidu-entity-search-competition) to project page.


10-fold cross validation experiment, and testing on hold-out set.
```sh
python run_experiment.py --extractors=e1,e2...
```
Output:
```
Experiment ID: 101. Detailed report at reports/101.html. Model at models/101.model

Cross validation:
| task1      | task2     | ...
| 0.70+-0.01 | 0.80+-0.02| ...

Hold-out set:
| task1    | task2    | ...
| 0.70     | 0.80     | ...

```

Listing past experiment result overview.

```sh
python experiments_summary.py --export_to=reports/summary.html
```
Output will be in `reports/summary.html`
```
Evaluation result on hold-out set:
| Exp ID | Features | task1  | task2 | ...  |
| 101    | e1,e2,... |
```

Export result
```sh
python export_result.py --model_id=101 --test_dir=data/DEV\ SET --output_dir=output
```

