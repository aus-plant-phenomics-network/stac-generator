# stac-generator

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
