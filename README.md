# stac-generator

## Run example

First [install packages](#install-pdm-and-all-packages). Once completed, active the environment with

```bash
source .venv/bin/activate
```

Run the example csv:

```bash
python main.py csv example/csv/source_config.csv --to_local example/generated --id csv_point_data
```

View CLI help
```bash
python main.py --help
```

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
