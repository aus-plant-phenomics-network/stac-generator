
## Overview

[STAC](https://stacspec.org/en) is a metadata standard for describing spatio-temporal assets, particularly satellite imagery and other Earth observation data. The goal of STAC is to make it easier for users to search, discover and use geospatial assets by providing a consistent and standardised way to catalog and query them. 

`stac_generator` is a Python package that allows users to generate STAC-compliant metadata from raw assets and store them either locally or behind a STAC API compliant [server](https://github.com/stac-utils/stac-fastapi-pgstac). 

The `stac_generator` is developed as part of the Multiscalar Crop Characterisation Network (MCCN) project, serving as the frontend metadata building tool for generating spatial datacube. For more information on the MCCN project, please visit [here](#).

The `stac_generator` was developed as part of the Multiscalar Crop Characterisation Project (MCCN). Using the STAC generator to describe an asset collection is the first step in building a datacube with the MCCN engine.

## Installation

Requirements: python3.11+

STAC Generator can be installed directly from Pypi:

```
pip install stac_generator
```

Note that if you want STAC Generator to be accessible from everywhere (outside the environment where it is installed), you can install STAC Generator with pipx instead of pip. To install pipx, visit [this](https://pipx.pypa.io/stable/installation/).

```
pipx install stac_generator
```
