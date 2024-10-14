# stac-generator

## Install Package

```bash
pip install pystac_generator
```

Note: stac-generator name is already used by someone else.

## Run as CLI

```bash
stac_generator --help
```

## Run as python package

```python
from stac_generator.generator_factor import StacGeneratorFactory
```

## Run the current example

Note that you will need to either clone the repository or download the [example](./example/) directory in the repository

To run the example as CLI

```bash
stac_generator csv example/csv/source_config.csv --id point_data --to_local generated
```

To run the example as python module: see the [notebook](./demo_csv.ipynb)

## Install pdm and all packages

```bash
make install
```

## Adding a new dependency

```bash
pdm add <package>
```

## Adding a new dependency under a dependency group:

```bash
pdm add -dG <group> <package>
```

## Remove a dependency

```bash
pdm remove <package>
```

## Serve docs locally

```bash
make docs
```

## Fixing CI

Run the linter. This runs all methods in pre-commit - i.e. checking for exports, format the code, etc, followed by mypy. This has a one to one correspondence with validate-ci

```bash
make lint
```

Run tests. This runs all tests using pytest. This has a one to one correspondence with test-ci

```bash
make test
```
