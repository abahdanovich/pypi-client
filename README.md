PyPI client
===========

![Lint](https://github.com/abahdanovich/pypi-client/workflows/Lint/badge.svg)
![Test](https://github.com/abahdanovich/pypi-client/workflows/Test/badge.svg)

CLI tool for searching for a python package by name.

* fetches all package names from PyPi
* filters and finds matching packages (by name)
* downloads github stars (if package uses GH as a repo) number and package downloads
* shows results in a table or json

Install
-------

```
pip install pypi-client
```

Usage
-----

```
Usage: pypi-client [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  auth-github  Log into GitHub
  search       Search python package by name
```

Search
------

```
Usage: pypi-client search [OPTIONS] NAME_SEARCH

  Search python package by name

Options:
  --limit INTEGER RANGE           Max number of items to return
  --no-cache                      Clear cache before run
  --log-level [ERROR|WARN|INFO|DEBUG]
                                  Logging level
  --json                          Return in json format
  --threads INTEGER               Number of threads to use
  --help                          Show this message and exit.
```

Example output:

```
$ pypi-client search kafka
Found 155 packages:
name                                 downloads  summary                                                version      home_page                                                stars    releases  last_release_date
---------------------------------  -----------  -----------------------------------------------------  -----------  -----------------------------------------------------  -------  ----------  -------------------
kafka-python                           6863094  Pure Python client for Apache Kafka                    2.0.2        https://github.com/dpkp/kafka-python                      4084          34  2020-09-30
confluent-kafka                        3341286  Confluent's Python client for Apache Kafka             1.5.0        https://github.com/confluentinc/confluent-kafka-py...     2017          20  2020-08-07
ns-kafka-python                           5739  Pure Python client for Apache Kafka                    1.4.7        https://github.com/dpkp/kafka-python                      4084           1  2020-09-28
tencentcloud-sdk-python-ckafka           11820  Tencent Cloud Ckafka SDK for Python                    3.0.290      https://github.com/TencentCloud/tencentcloud-sdk-p...      297          40  2020-11-12
kafka                                   939197  Pure Python client for Apache Kafka                    1.3.5        https://github.com/dpkp/kafka-python                      4084          17  2017-10-07
[...]
```