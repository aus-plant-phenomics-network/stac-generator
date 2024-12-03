# stac-generator

Documentation [page](https://aus-plant-phenomics-network.github.io/stac-generator/)

Examples of stac generator [configs](./example/configs/) in csv/json/yaml

Examples of generated stac items for [point]() data, [vector]() data, [raster]() data

## CLI Commands

Generating point collection and push to remote

```bash
pdm run stac_generator https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/unit_tests/point/config/point_data_config.json --dst http://115.146.84.224:8082 --id test_point_data -v
```

Generating vector collection and push to remote

```bash
pdm run stac_generator https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/unit_tests/vector/config/vector_config.json --dst http://115.146.84.224:8082 --id test_vector_data
```

## For developers

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
