
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
