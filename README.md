# stac-generator

## Install Package

```bash
pip install pystac_generator
```


## Run as CLI

```bash
stac_generator --help
```

## Run as python package

```python
from stac_generator.generator_factor import StacGeneratorFactory
```

## Run the current example as a Python module

Note that you will need to either clone the repository or download the [example](./example/) directory in the repository

To run the example as python module: see the [notebook](./demo_csv.ipynb)

## Run the current example as a CLI 

### When the source file is on local host:

See the [config](./example/csv/source_config.csv) file. Note how the location points to a file on local host. 

```bash
stac_generator csv example/csv/source_config.csv --to_local example/csv/generated --id point_data
```

### When the source file is hosted and accessible via http(s) (AWS S3, Nectr Object Storage):

See the [config](./example//csv/remote_config.csv) file. Note how the location points to a remote file.

```bash
stac_generator csv example/csv/remote_config.csv --to_local example/csv/generated --id point_data
```

### When the config file is hosted and accessible via http(s) (AWS S3, Nectr Object Storage):

So far, the config files are stored locally. It is possible to have the config file hosted somewhere. 

```bash
stac_generator csv https://object-store.rc.nectar.org.au/v1/AUTH_9f063fd4ed28439487e49cddfb56d02d/Test_Data_Container/csv/remote_config.csv --to_local example/csv/generated --id point_data
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
