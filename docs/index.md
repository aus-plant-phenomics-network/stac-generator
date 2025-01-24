
## Overview

`stac_generator` is a command line interface (CLI) program to automatically generate [STAC](https://stacspec.org/en)-compliant metadata for geospatial datasets. `stac_generator` provides the following features: 

- Generating STAC descriptions for raster (tif), vector (shp, geojson, zip+shp), and point data (csv, txt).

- Saving generated STAC records locally as jsons or POST/PUT them to a STAC compliant API server.

- Generating compliant metadata for datacube construction with the MCCN engine. 

Using the STAC generator to describe a dataset is the first step in building a datacube with the MCCN engine. 

While most STAC information can be derived directly from the data, other information such as licensing, instrumentation, and ids (collection id/item id) does not come with the data and must be provided along side. We make the distinction between the following types of metadata:

- STAC Collection Metadata: metadata at the collection level. Collection level metadata is provided as input in the CLI. 

- STAC Item Metadata: metadata at the item level. Item level metadata is provided as row/entry in the metadata file. 



## Workflow

The process for generating STAC descriptions for a dataset is as follows: 

- Prepare assets:

  - Determine what assets (tif images, vector boundaries, csv records) are important for the project. For instance, this can be all raw/processed data used in the project. Alternatively, this includes all data you want to load into the data cube. 

  - Host required assets somewhere with a semi-permanent URI. In general, if you want the data to be publicly accessible, the assets should be hosted on some cloud object storage - i.e S3, Nectar, etc. Otherwise, the asset only needs to be hosted somewhere accessible by the machine running the STAC Generator. 

- Prepare Item level metadata:

  - Depending on whether the data item is raster/vector/point, the corresponding documentations can be useful. At the very least, you should think about the item id, asset location - i.e the link to where the asset is hosted, and the date and time when the item was collected. 

- Prepare Collection level metadata:

  - The relevant documentation page (to be added) may be helpful. At the very least, collection id needs to be provided. 

- Determine whether to save the STAC records locally or remotely. 



## Installation

Requirements: python3.10+ 

STAC Generator can be installed directly from Pypi: 

```
pip install stac_generator
```

Note that if you want STAC Generator to be accessible from everywhere (outside the environment where it is installed), you can install STAC Generator with pipx instead of pip. To install pipx, visit [this](https://pipx.pypa.io/stable/installation/). 

```
pipx install stac_generator 
```