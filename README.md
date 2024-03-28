# Bmt-py

<p align="center">
    <em>Binary Merkle Tree operations on data</em>
</p>

<div align="center">

| Feature       | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Technology    | [![Python](https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org/) [![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat&logo=GitHub-Actions&logoColor=white)](https://github.com/features/actions) [![Pytest](https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat&logo=Pytest&logoColor=white)](https://github.com/alienrobotninja/bee-py/actions/workflows/tests.yml/badge.svg)                             |
| Linting       | [![Code style: black](https://img.shields.io/badge/Code%20Style-black-000000.svg)](https://github.com/psf/black) ![Style Guide](https://img.shields.io/badge/Style%20Guide-Flake8-blue) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)                                                                                                                                                                                                                                                                                                                                                                              |
                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| CI/CD         | [![Tests](https://github.com/alienrobotninja/bee-py/actions/workflows/tests.yml/badge.svg)](https://github.com/alienrobotninja/bee-py/actions/workflows/tests.yml) [![Labeler](https://github.com/alienrobotninja/bee-py/actions/workflows/labeler.yml/badge.svg)](https://github.com/alienrobotninja/bee-py/actions/workflows/labeler.yml) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)                                                                                                                                                                                                            |
| Docs          | [![Read the Docs](https://img.shields.io/readthedocs/bee-py/latest.svg?label=Read%20the%20Docs)](https://bee-py.readthedocs.io/)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Package       | [![PyPI - Version](https://img.shields.io/pypi/v/bee-py.svg)](https://pypi.org/project/bee-Py/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bee-Py)](https://pypi.org/project/bee-py/) [![PyPI - License](https://img.shields.io/pypi/l/bee-Py)](https://pypi.org/project/bee-py/)                                                                                                                                                                                                                                                                                                                                                                                                        |
| Meta          | [![GitHub license](https://img.shields.io/github/license/alienrobotninja/bee-py?style=flat&color=1573D5)](https://github.com/alienrobotninja/bee-py/blob/main/LICENSE) [![GitHub last commit](https://img.shields.io/github/last-commit/alienrobotninja/bee-py?style=flat&color=1573D5)](https://github.com/alienrobotninja/bee-py/commits/main) [![GitHub commit activity](https://img.shields.io/github/commit-activity/m/alienrobotninja/bee-py?style=flat&color=1573D5)](https://github.com/alienrobotninja/bee-py/graphs/commit-activity) [![GitHub top language](https://img.shields.io/github/languages/top/alienrobotninja/bee-py?style=flat&color=1573D5)](https://github.com/alienrobotninja/bee-py) |

</div>

---

**Documentation**: <a href="https://aviksaikat.github.io/bmt_py/" target="_blank">https://aviksaikat.github.io/bmt_py/</a>

**Source Code**: <a href="https://github.com/aviksaikat/bmt_py" target="_blank">https://github.com/aviksaikat/bmt_py</a>

---

## Development

### Setup environment

We use [Hatch](https://hatch.pypa.io/latest/install/) to manage the development environment and production build. Ensure it's installed on your system.

### Run unit tests

You can run all the tests with:

```bash
hatch run test
```

### Format the code

Execute the following command to apply linting and check typing:

```bash
hatch run lint
```

### Publish a new version

You can bump the version, create a commit and associated tag with one command:

```bash
hatch version patch
```

```bash
hatch version minor
```

```bash
hatch version major
```

Your default Git text editor will open so you can add information about the release.

When you push the tag on GitHub, the workflow will automatically publish it on PyPi and a GitHub release will be created as draft.

## Serve the documentation

You can serve the Mkdocs documentation with:

```bash
hatch run docs-serve
```

It'll automatically watch for changes in your code.

## License

This project is licensed under the terms of the BSD license.
