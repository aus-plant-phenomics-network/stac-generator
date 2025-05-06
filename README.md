# STAC Generator

<!-- markdownlint-disable -->
<p align="center">
  <!-- github-banner-start -->
  <!-- github-banner-end -->
</p>
<!-- markdownlint-restore -->

<div align="center">

<!-- prettier-ignore-start -->

| Project |     | Status|
|---------|:----|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CI/CD   |     | [![CI](https://github.com/aus-plant-phenomics-network/stac-generator/actions/workflows/github-actions.yml/badge.svg)](https://github.com/aus-plant-phenomics-network/stac-generator/actions/workflows/github-actions.yml) [![documentation](https://github.com/aus-plant-phenomics-network/stac-generator/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/aus-plant-phenomics-network/stac-generator/actions/workflows/pages/pages-build-deployment) |

<!-- prettier-ignore-end -->
</div>

<hr>

Check out the [documentation 📚](https://aus-plant-phenomics-network.github.io/stac-generator/)

Examples of stac generator [configs](./example) in csv/json/yaml

## Overview

[STAC](https://stacspec.org/en) is a json-based metadata standard for describing spatial-temporal assets, particularly satellite and Earth observation data. STAC allows users to quickly search, discover and use geospatial assets by providing a consistent structure for query and storage.

The stac_generator can be used as a cross-platform command line interface (CLI) program or a python library that combines automatically extracted geospatial information from raw assets and other user-provided metadata to build a STAC-compliant metadata record for further use. Generated STAC records can be saved locally or behind a STAC API-compliant server.

The stac_generator was developed as part of the Multiscalar Crop Characterisation Project (MCCN). Using the STAC generator to describe an asset collection is the first step in building a datacube with the MCCN engine.

## Installation

Requirements: python3.11-3.12

STAC Generator can be installed directly from Pypi:

``` { .sh }
pip install pystac-generator
```

Note that if you want STAC Generator to be accessible from everywhere (outside the environment where it is installed), you can install STAC Generator with pipx instead of pip. To install pipx, visit [this](https://pipx.pypa.io/stable/installation/).

``` { .sh }
pipx install pystac-generator
```

## Upgrade

Using pip:

``` { .sh}
pip install pystac-generator --upgrade
```

Using pipx:

``` { .sh}
pipx upgrade pystac-generator
```



## For developers

We use [pdm](https://pdm-project.org/en/latest/#installation) as the project's package manager.

Clone:

```bash
git clone https://github.com/aus-plant-phenomics-network/stac-generator.git
```

Install dependencies:

```bash
pdm install
```

Run tests:

```bash
make test
```

Run static analysis

```bash
make lint
```
